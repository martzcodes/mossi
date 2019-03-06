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

dir_name = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
curr_semester = sys.argv[3]

# Configure here:
userid = -1  # insert user id here
# End Configure

# folders should be organized as assignment-semester-year/part1/<part1 files>, assignment-semester-year/part2/<part2 files>, etc
# each part should have an object below

submission_files = {}
assignment_files = {}
assignment_parts = []

# need to parse out assignment structure
for path, dir_list, file_list in os.walk(dir_name):
    temp_dir = dir_name
    if not dir_name.endswith('/'):
        temp_dir += '/'
    if path.startswith(temp_dir):
        structure_raw = path.split(temp_dir)[-1]
        structure = structure_raw.split('/')
        if len(structure) > 1:
            assignment_file = structure[0]
            semester = structure[1]
            if structure_raw.find(curr_semester) != -1:
                if len(structure) > 2:
                    submission = structure[2]
                    if assignment_file not in submission_files:
                        submission_files[assignment_file] = {}
                    submission_files[assignment_file][submission] = path + '/*.py'
            else:
                if assignment_file not in assignment_files:
                    assignment_files[assignment_file] = []
                assignment_files[assignment_file].append(path + '/*.py')

for assignment_file, submissions in submission_files.items():
    for submission_key, submission in submissions.items():
        assignment_parts.append({
            "name": assignment_file,  # will be used for a subfolder
            "submission": int(submission_key.split('sub')[1]),
            # add base files (code to be ignored) here, relative path
            "basefiles": [],
            "files": [],  # add specific files here, relative path
            # add files with wildcards here, relative path
            "filesByWildcard": [submission] + assignment_files[assignment_file]
        })

# you may need to adjust this based on your files naming conventions... the file naming scheme for this was:
# studentname_id_course_assignmentPart#-.py
# when used with mossi this becomes  filepath/studentname_id_course_assignmentPart#-.py (##%)


def parse_path(file_ref):
    actual_file = file_ref.split("/")[-1]
    student_uuid = actual_file.split("_")[0]
    percent = int(actual_file.split("(")[1].split("%")[0])
    file_path = actual_file.split(" (")[0].split(student_uuid)[1]
    current = file_ref.find(curr_semester) != -1
    watermark = file_ref.find('watermark') != -1
    return actual_file, student_uuid, percent, file_path, current, watermark


moss_urls = {}
urls = []
anonpairs = []
studentsanon = {}
uuid_percents = {a: [] for a in range(100)}
uuid_lines = {}
anon_lines = {}
anon_line_refs = {}

for assignment_part in assignment_parts:
    m = mosspy.Moss(userid, "python")

    m.setIgnoreLimit(75)
    m.setNumberOfMatchingFiles(250)  # should return 250 results

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

    urls.append((assignment_part['name'], url))

    print("Moss finished {}: {}".format(assignment_part['name'], url))

    if assignment_part['name'] not in moss_urls:
        moss_urls[assignment_part['name']] = {}
    moss_urls[assignment_part['name']]['sub{}'.format(
        assignment_part['submission'])] = url

    # Save report file
    # m.saveWebPage(url, "mosspy/report.html")

    # Download whole report locally including code diff links

    if not os.path.exists(os.path.join(OUTPUT_DIR, assignment_part['name'], "{}".format(assignment_part['submission']))):
        try:
            os.makedirs(os.path.join(OUTPUT_DIR, assignment_part['name'], "{}".format(assignment_part['submission'])))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    mosspy.download_report(url, "{}/{}/{}".format(OUTPUT_DIR, assignment_part['name'], assignment_part['submission']), connections=8)

    report = "{}/{}/{}/index.html".format(
        OUTPUT_DIR, assignment_part['name'], assignment_part['submission'])
    soup = BeautifulSoup(open(report), 'lxml')
    for row in soup.find_all(['tr']):
        row_students = []
        line_match = 0
        for td in row.find_all('td', {'align': 'right'}):
            line_match = int(td.string)
        for anchor in row.find_all(['a']):
            if anchor.string.find("/") != -1:
                actual_file, student_uuid, percent, file_path, current, watermark = parse_path(
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
                if anonpair not in anonpairs:
                    anonpairs.append(anonpair)

            if row_students[0]['student'] != row_students[1]['student']:
                for row_student in row_students:
                    current, percent, student_uuid, student, line_match = row_student['current'], row_student[
                        'percent'], row_student['uuid'], row_student['student'], row_student['lines']
                    if current:
                        if student_uuid not in uuid_percents[percent]:
                            uuid_percents[percent].append(student_uuid)
                        if line_match not in uuid_lines:
                            uuid_lines[line_match] = []
                        if student_uuid not in uuid_lines[line_match]:
                            uuid_lines[line_match].append(student_uuid)

            if row_students[0]['student'] != row_students[1]['student']:
                if row_students[0]['student'] not in studentsanon:
                    studentsanon[row_students[0]['student']] = {}
                if row_students[0]['file'] not in studentsanon[row_students[0]['student']]:
                    studentsanon[row_students[0]['student']
                                 ][row_students[0]['file']] = []
                studentsanon[row_students[0]['student']][row_students[0]['file']].append({
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
                if row_students[1]['student'] not in studentsanon:
                    studentsanon[row_students[1]['student']] = {}
                if row_students[1]['file'] not in studentsanon[row_students[1]['student']]:
                    studentsanon[row_students[1]['student']
                                 ][row_students[1]['file']] = []
                studentsanon[row_students[1]['student']][row_students[1]['file']].append({
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
    for top_path in glob.iglob('{}/{}/{}/match*-top.html'.format(OUTPUT_DIR, assignment_part['name'], assignment_part['submission']), recursive=True):
        soup = BeautifulSoup(open(top_path), 'lxml')
        line_refs = []
        for header in soup.find_all(['th']):
            if len(header.text) > 1 and header.find('img') is None:
                actual_file, student_uuid, percent, file_path, current, watermark = parse_path(
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

            if line_refs[0]['student'] not in anon_line_refs:
                anon_line_refs[line_refs[0]['student']] = []
            anon_line_refs[line_refs[0]['student']].append(line_refs)

            if line_refs[1]['student'] not in anon_line_refs:
                anon_line_refs[line_refs[1]['student']] = []
            anon_line_refs[line_refs[1]['student']].append(
                [line_refs[1], line_refs[0]])

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open('{}/student-anon.json'.format(OUTPUT_DIR), 'w') as outfile:
        json.dump(studentsanon, outfile, indent=4, sort_keys=True)

    with open('{}/uuid-percents.json'.format(OUTPUT_DIR), 'w') as outfile:
        json.dump(uuid_percents, outfile, indent=4, sort_keys=True)

    with open('{}/uuid-lines.json'.format(OUTPUT_DIR), 'w') as outfile:
        json.dump(uuid_lines, outfile, indent=4, sort_keys=True)

    with open('{}/student-anon-pairs.json'.format(OUTPUT_DIR), 'w') as outfile:
        json.dump({"pairs": anonpairs}, outfile, indent=4, sort_keys=True)

    with open('{}/moss-urls.json'.format(OUTPUT_DIR), 'w') as outfile:
        json.dump(moss_urls, outfile, indent=4, sort_keys=True)

    with open('./polygonrobot/anon-line-refs.json', 'w') as outfile:
        json.dump(anon_line_refs, outfile, indent=4, sort_keys=True)

    with open('{}/student-anon-groups.json'.format(OUTPUT_DIR), 'w') as outfile:
        out_dict = find_student_groups(anonpairs)
        json.dump(out_dict, outfile, indent=4, sort_keys=True)

    with open('{}/multi-student-collaborations.json'.format(OUTPUT_DIR), 'w') as outfile:
        out_dict = find_multistudent_collaborations(anon_line_refs)
        json.dump(out_dict, outfile, indent=4, sort_keys=True)


for url in urls:
    print("{}: {}".format(url[0], url[1]))
