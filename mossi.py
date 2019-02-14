import mosspy
import glob
from bs4 import BeautifulSoup
import os
import os.path
import json
import uuid
import errno
import pdfkit


### Configure here: 
userid = -1 # insert user id here
OUTPUT = "test_assignment" # output folder
curr_assignment = 'test-spring-2019' # folder name of the current assignment

# folders should be organized as assignment-semester-year/part1/<part1 files>, assignment-semester-year/part2/<part2 files>, etc
# each part should have an object below

assignment_parts = [
    {
        "name": "part3", # will be used for a subfolder
        "basefiles": [], # add base files (code to be ignored) here, relative path
        "files": [], # add specific files here, relative path
        "filesByWildcard": ['test_assignment/**/part3/*.py'] #add files with wildcards here, relative path
    },
    {
        "name": "part4", # will be used for a subfolder
        "basefiles": [], # add base files (code to be ignored) here, relative path
        "files": [], # add specific files here, relative path
        "filesByWildcard": ['test_assignment/**/part4/*.py'] #add files with wildcards here, relative path
    }
]

# you may need to adjust this based on your files naming conventions... the file naming scheme for this was:
# studentname_id_course_assignmentPart#-.py
# when used with mossi this becomes  filepath/studentname_id_course_assignmentPart#-.py (##%)

def parse_path(file_ref):
    actual_file = file_ref.split("/")[-1]
    student = actual_file.split("_")[0]
    if student not in uuids:
        uuids[student] = str(uuid.uuid4())
    student_uuid = uuids[student]
    percent = int(actual_file.split("(")[1].split("%")[0])
    file_path = actual_file.split(" (")[0].split(student)[1]
    current = file_ref.find(curr_assignment) != -1
    return actual_file, student, student_uuid, percent, file_path, current


### End Configure

urls = []
students = {}
uuids = {}
if os.path.exists('{}/student-uuids.json'.format(OUTPUT)):
    with open('{}/student-uuids.json'.format(OUTPUT), 'r') as f:
        uuids = json.load(f)
uuid_percents = { a:[] for a in range(100)}
student_percents = { a:[] for a in range(100)}
uuid_lines = {}
student_lines = {}
student_line_refs = {}

for assignment_part in assignment_parts:
    m = mosspy.Moss(userid, "python")

    m.setIgnoreLimit(50)

    for base in assignment_part['basefiles']:
        m.addBaseFile(base)
    
    for specific in assignment_part['files']:
        m.addFile(specific)
    
    for wildcard in assignment_part['filesByWildcard']:
        m.addFilesByWildcard(wildcard)    

    url = m.send() # Submission Report URL

    urls.append((assignment_part['name'], url))

    print("Moss finished {}: {}".format(assignment_part['name'], url))

    # Save report file
    # m.saveWebPage(url, "mosspy/report.html")

    # Download whole report locally including code diff links

    if not os.path.exists(os.path.join(OUTPUT, assignment_part['name'])):
        try:
            os.makedirs(os.path.join(OUTPUT, assignment_part['name']))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    mosspy.download_report(url, "{}/{}".format(OUTPUT, assignment_part['name']), connections=8)

    report = "{}/{}/index.html".format(OUTPUT, assignment_part['name'])
    soup = BeautifulSoup(open(report), 'lxml')
    for row in soup.find_all(['tr']):
        row_students = []
        line_match = 0
        for td in row.find_all('td', {'align': 'right'}):
            line_match = int(td.string)
        for anchor in row.find_all(['a']):
            if anchor.string.find("/") != -1:
                actual_file, student, student_uuid, percent, file_path, current = parse_path(anchor.string)
                match = anchor.get('href')
                if current:
                    if student_uuid not in uuid_percents[percent]:
                        uuid_percents[percent].append(student_uuid)
                    if student not in student_percents[percent]:
                        student_percents[percent].append(student)
                    if line_match not in uuid_lines:
                        uuid_lines[line_match] = []
                        student_lines[line_match] = []
                    if student_uuid not in uuid_lines[line_match]:
                        uuid_lines[line_match].append(student_uuid)
                    if student not in student_lines[line_match]:
                        student_lines[line_match].append(student)
                row_students.append({
                    'student': student,
                    'file': file_path,
                    'report': report,
                    'match': match,
                    'percent': percent,
                    'lines': line_match,
                    'current': current
                })
        if len(row_students) == 2:
            if row_students[0]['student'] not in students:
                students[row_students[0]['student']] = {}
            if row_students[0]['file'] not in students[row_students[0]['student']]:
                students[row_students[0]['student']][row_students[0]['file']] = []
            students[row_students[0]['student']][row_students[0]['file']].append({
                'current':row_students[0]['current'], 
                'report': row_students[0]['report'],
                'match': row_students[0]['match'],
                'percent': row_students[0]['percent'],
                'lines': row_students[0]['lines'],
                'other_student': row_students[1]
            })

            if row_students[1]['student'] not in students:
                students[row_students[1]['student']] = {}
            if row_students[1]['file'] not in students[row_students[1]['student']]:
                students[row_students[1]['student']][row_students[1]['file']] = []
            students[row_students[1]['student']][row_students[1]['file']].append({
                'current':row_students[1]['current'], 
                'report': row_students[1]['report'],
                'match': row_students[1]['match'],
                'percent': row_students[1]['percent'],
                'lines': row_students[1]['lines'],
                'other_student': row_students[0]
            })
    for top_path in glob.iglob('{}/{}/match*-top.html'.format(OUTPUT, assignment_part['name']), recursive=True):
        soup = BeautifulSoup(open(top_path), 'lxml')
        line_refs = []
        for header in soup.find_all(['th']):
            if len(header.text) > 1 and header.find('img') is None:
                actual_file, student, student_uuid, percent, file_path, current = parse_path(header.string)
                student_lines = {
                    'student': student,
                    'file_path': header.text.split(' (')[0],
                    'assignment': actual_file.split('_')[-1].split('.py')[0],
                    'percent': percent,
                    'lines': {}
                }
                line_refs.append(student_lines)
        for row in soup.find_all('a', href=True):
            if len(row.text) > 0:
                line_refs[int(row.get('target'))]['lines'][row.get('name')] = {
                    'from': int(row.text.split('-')[0]),
                    'to': int(row.text.split('-')[1])
                }
        if line_refs[0]['student'] not in student_line_refs:
            student_line_refs[line_refs[0]['student']] = []
        student_line_refs[line_refs[0]['student']].append(line_refs)
        
        if line_refs[1]['student'] not in student_line_refs:
            student_line_refs[line_refs[1]['student']] = []
        student_line_refs[line_refs[1]['student']].append([line_refs[1], line_refs[0]])

with open('{}/student.json'.format(OUTPUT), 'w') as outfile:
    json.dump(students, outfile, indent=4, sort_keys=True)

with open('{}/student-uuids.json'.format(OUTPUT), 'w') as outfile:
    json.dump(uuids, outfile, indent=4, sort_keys=True)

with open('{}/uuid-percents.json'.format(OUTPUT), 'w') as outfile:
    json.dump(uuid_percents, outfile, indent=4, sort_keys=True)

with open('{}/student-percents.json'.format(OUTPUT), 'w') as outfile:
    json.dump(student_percents, outfile, indent=4, sort_keys=True)

with open('{}/uuid-lines.json'.format(OUTPUT), 'w') as outfile:
    json.dump(uuid_lines, outfile, indent=4, sort_keys=True)

with open('{}/student-lines.json'.format(OUTPUT), 'w') as outfile:
    json.dump(student_lines, outfile, indent=4, sort_keys=True)

with open('{}/student-line-refs.json'.format(OUTPUT), 'w') as outfile:
    json.dump(student_line_refs, outfile, indent=4)

for url in urls:
    print("{}: {}".format(url[0], url[1]))