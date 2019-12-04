import sys
import mosspy
import glob
from bs4 import BeautifulSoup
import os
import os.path
import json
import uuid
import errno
import pdfkit
from graph_functions import find_student_groups, find_multistudent_collaborations

class Mossi(object):
    def __init__(self, moss_user, dir_name, output_dir, curr_semester, base_file = None):
        self.userid = moss_user
        self.dir_name = dir_name
        self.output_dir = output_dir
        self.curr_semester = curr_semester
        self.base_file = base_file

        self.submission_files = {}
        self.assignment_files = {}
        self.assignment_parts = []

        self.moss_urls = {}
        self.urls = []
        self.anonpairs = []
        self.studentsanon = {}
        self.uuid_percents = {a: [] for a in range(100)}
        self.uuid_lines = {}
        self.anon_line_refs = {}
        
    def pre_process(self):
        # need to parse out assignment structure
        for path, dir_list, file_list in os.walk(self.dir_name):
            temp_dir = self.dir_name
            if not self.dir_name.endswith('/'):
                temp_dir += '/'
            if path.startswith(temp_dir):
                structure_raw = path.split(temp_dir)[-1]
                structure = structure_raw.split('/')
                if len(structure) > 1:
                    assignment_file = structure[0]
                    semester = structure[1]
                    if structure_raw.find(self.curr_semester) != -1:
                        if len(structure) > 2:
                            submission = structure[2]
                            if assignment_file not in self.submission_files:
                                self.submission_files[assignment_file] = {}
                            self.submission_files[assignment_file][submission] = path + '/*.py'
                    else:
                        if assignment_file not in self.assignment_files:
                            self.assignment_files[assignment_file] = []
                        self.assignment_files[assignment_file].append(path + '/*.py')
        print(self.submission_files)

        for assignment_file, submissions in self.submission_files.items():
            for submission_key, submission in submissions.items():
                self.assignment_parts.append({
                    "name": assignment_file,  # will be used for a subfolder
                    "submission": int(submission_key.split('sub')[1]),
                    # add base files (code to be ignored) here, relative path
                    "basefiles": [],
                    "files": [],  # add specific files here, relative path
                    # add files with wildcards here, relative path
                    "filesByWildcard": [submission] + self.assignment_files[assignment_file]
                })

        # you may need to adjust this based on your files naming conventions... the file naming scheme for this was:
        # studentname_id_course_assignmentPart#-.py
        # when used with mossi this becomes  filepath/studentname_id_course_assignmentPart#-.py (##%)

        return True


    def parse_path(self, file_ref):
        actual_file = file_ref.split("/")[-1]
        student_uuid = actual_file.split("_")[0]
        percent = int(actual_file.split("(")[1].split("%")[0])
        file_path = actual_file.split(" (")[0].split(student_uuid)[1]
        current = file_ref.find(self.curr_semester) != -1
        watermark = file_ref.find('watermark') != -1
        return actual_file, student_uuid, percent, file_path, current, watermark

    def moss(self):
        try:
            for assignment_part in self.assignment_parts:
                m = mosspy.Moss(self.userid, "python")

                m.setIgnoreLimit(50)
                m.setNumberOfMatchingFiles(250)  # should return 250 results

                if self.base_file is not None:
                    m.addBaseFile(self.base_file)

                for base in assignment_part['basefiles']:
                    m.addBaseFile(base)

                for specific in assignment_part['files']:
                    m.addFile(specific)

                temp_files = []
                for wildcard in assignment_part['filesByWildcard']:
                    print("Uploading: {}".format(wildcard))
                    m.addFilesByWildcard(wildcard)

                    for file in glob.glob(wildcard):
                        temp_files.append((file, None))

                print("Files: {}".format(len(temp_files)))
                del temp_files

                url = m.send()  # Submission Report URL

                self.urls.append((assignment_part['name'], url))

                print("Moss finished {}: {}".format(assignment_part['name'], url))

                if assignment_part['name'] not in self.moss_urls:
                    self.moss_urls[assignment_part['name']] = {}
                self.moss_urls[assignment_part['name']]['sub{}'.format(
                    assignment_part['submission'])] = url

                # Save report file
                # m.saveWebPage(url, "mosspy/report.html")

                # Download whole report locally including code diff links

                if not os.path.exists(os.path.join(self.output_dir, assignment_part['name'], "{}".format(assignment_part['submission']))):
                    try:
                        os.makedirs(os.path.join(self.output_dir, assignment_part['name'], "{}".format(assignment_part['submission'])))
                    except OSError as exc:  # Guard against race condition
                        if exc.errno != errno.EEXIST:
                            raise
                mosspy.download_report(url, "{}/{}/{}".format(self.output_dir, assignment_part['name'], assignment_part['submission']), connections=8)
            
            for url in self.urls:
                print("{}: {}".format(url[0], url[1]))
        except:
            return False
        
        # return True if successful
        return True


    def post_process(self):
        for assignment_part in self.assignment_parts:
            report = "{}/{}/{}/index.html".format(
                self.output_dir, assignment_part['name'], assignment_part['submission'])
            soup = BeautifulSoup(open(report), 'lxml')
            for row in soup.find_all(['tr']):
                row_students = []
                line_match = 0
                for td in row.find_all('td', {'align': 'right'}):
                    line_match = int(td.string)
                for anchor in row.find_all(['a']):
                    if anchor.string.find("/") != -1:
                        actual_file, student_uuid, percent, file_path, current, watermark = self.parse_path(
                            anchor.string)
                        match = anchor.get('href')
                        row_students.append({
                            'file': file_path,
                            'report': report,
                            'match': match,
                            'percent': percent,
                            'lines': line_match,
                            'current': current,
                            'student': student_uuid,
                            'watermark': watermark
                        })

                if len(row_students) == 2:
                    if (row_students[0]['percent'] > 40 or row_students[1]['percent'] > 40) and row_students[0]['student'] != row_students[1]['student']:
                        anonpair = [row_students[0]['student'], row_students[1]['student']]
                        anonpair.sort()
                        if anonpair not in self.anonpairs:
                            self.anonpairs.append(anonpair)

                    if row_students[0]['student'] != row_students[1]['student']:
                        for row_student in row_students:
                            current, percent, student_uuid, line_match = row_student['current'], row_student[
                                'percent'], row_student['student'], row_student['lines']
                            if current:
                                if student_uuid not in self.uuid_percents[percent]:
                                    self.uuid_percents[percent].append(student_uuid)
                                if line_match not in self.uuid_lines:
                                    self.uuid_lines[line_match] = []
                                if student_uuid not in self.uuid_lines[line_match]:
                                    self.uuid_lines[line_match].append(student_uuid)

                    if row_students[0]['student'] != row_students[1]['student']:
                        if row_students[0]['student'] not in self.studentsanon:
                            self.studentsanon[row_students[0]['student']] = {}
                        if row_students[0]['file'] not in self.studentsanon[row_students[0]['student']]:
                            self.studentsanon[row_students[0]['student']
                                        ][row_students[0]['file']] = []
                        self.studentsanon[row_students[0]['student']][row_students[0]['file']].append({
                            'current': row_students[0]['current'],
                            'assignment': assignment_part['name'],
                            'report': row_students[0]['report'],
                            'match': row_students[0]['match'],
                            'percent': row_students[0]['percent'],
                            'lines': row_students[0]['lines'],
                            'submission': assignment_part['submission'],
                            'student': row_students[0]['student'],
                            'other_student': row_students[1]
                        })
                        if row_students[1]['student'] not in self.studentsanon:
                            self.studentsanon[row_students[1]['student']] = {}
                        if row_students[1]['file'] not in self.studentsanon[row_students[1]['student']]:
                            self.studentsanon[row_students[1]['student']
                                        ][row_students[1]['file']] = []
                        self.studentsanon[row_students[1]['student']][row_students[1]['file']].append({
                            'current': row_students[1]['current'],
                            'assignment': assignment_part['name'],
                            'report': row_students[1]['report'],
                            'match': row_students[1]['match'],
                            'percent': row_students[1]['percent'],
                            'lines': row_students[1]['lines'],
                            'submission': assignment_part['submission'],
                            'student': row_students[1]['student'],
                            'other_student': row_students[0]
                        })
            for top_path in glob.iglob('{}/{}/{}/match*-top.html'.format(self.output_dir, assignment_part['name'], assignment_part['submission'])):
                soup = BeautifulSoup(open(top_path), 'lxml')
                line_refs = []
                for header in soup.find_all(['th']):
                    if len(header.text) > 1 and header.find('img') is None:
                        actual_file, student_uuid, percent, file_path, current, watermark = self.parse_path(
                            header.string)
                        student_refs = {
                            'student': student_uuid,
                            'file_path': header.text.split(' (')[0],
                            'assignment': actual_file.split('_')[-1].split('.py')[0],
                            'percent': percent,
                            'submission': assignment_part['submission'],
                            'watermark': watermark,
                            'lines': {}
                        }
                        line_refs.append(student_refs)
                if line_refs[0]['student'] != line_refs[1]['student']:
                    for row in soup.find_all('a', href=True):
                        if len(row.text) > 0:
                            line_refs[int(row.get('target'))]['lines'][row.get('name')] = {
                                'from': int(row.text.split('-')[0]),
                                'to': int(row.text.split('-')[1])
                            }

                    if line_refs[1]['student'] not in self.anon_line_refs:
                        self.anon_line_refs[line_refs[1]['student']] = {}
                    if line_refs[0]['student'] not in self.anon_line_refs[line_refs[1]['student']]:
                        self.anon_line_refs[line_refs[1]['student']][line_refs[0]['student']] = []
                    self.anon_line_refs[line_refs[1]['student']][line_refs[0]['student']].append(line_refs)

            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
        return True
    
    def output(self):
        with open('{}/student-anon.json'.format(self.output_dir), 'w') as outfile:
            json.dump(self.studentsanon, outfile, indent=4, sort_keys=True)

        with open('{}/uuid-percents.json'.format(self.output_dir), 'w') as outfile:
            json.dump(self.uuid_percents, outfile, indent=4, sort_keys=True)

        with open('{}/uuid-lines.json'.format(self.output_dir), 'w') as outfile:
            json.dump(self.uuid_lines, outfile, indent=4, sort_keys=True)

        with open('{}/student-anon-pairs.json'.format(self.output_dir), 'w') as outfile:
            json.dump({"pairs": self.anonpairs}, outfile, indent=4, sort_keys=True)

        with open('{}/moss-urls.json'.format(self.output_dir), 'w') as outfile:
            json.dump(self.moss_urls, outfile, indent=4, sort_keys=True)

        with open('{}/anon-line-refs.json'.format(self.output_dir), 'w') as outfile:
            json.dump(self.anon_line_refs, outfile, indent=4, sort_keys=True)

        with open('{}/student-anon-groups.json'.format(self.output_dir), 'w') as outfile:
            out_dict = find_student_groups(self.anonpairs)
            json.dump(out_dict, outfile, indent=4, sort_keys=True)

        with open('{}/multi-student-collaborations.json'.format(self.output_dir), 'w') as outfile:
            out_dict = find_multistudent_collaborations(self.anon_line_refs)
            json.dump(out_dict, outfile, indent=4, sort_keys=True)
        return True
