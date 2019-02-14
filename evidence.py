import glob
from bs4 import BeautifulSoup
import os
import os.path
import json
import uuid
import errno
import pdfkit

OUTPUT_FOLDER = 'mosspy'

students = {}
if os.path.exists('students.json'):
    with open('students.json', 'r') as f:
        students = json.load(f)
uuids = {}
if os.path.exists('student-uuids.json'):
    with open('student-uuids.json', 'r') as f:
        uuids = json.load(f)

student_line_refs = {}
if os.path.exists('student-line-refs.json'):
    with open('student-line-refs.json', 'r') as f:
        student_line_refs = json.load(f)

evidence = []
if os.path.exists('evidence.json'):
    with open('evidence.json', 'r') as f:
        evidence = json.load(f)['students']

for student in evidence:
    line_refs = student_line_refs[student]
    for line_ref in line_refs:
        student_A = line_ref[0]['student']
        student_B = uuids[line_ref[1]['student']]
        file_A = '{}/{}/{}/{}_A.py'.format(OUTPUT_FOLDER, student_A,student_B, line_ref[0]['assignment'])
        file_B = '{}/{}/{}/{}_B.py'.format(OUTPUT_FOLDER, student_A,student_B, line_ref[1]['assignment'])
        file_diff = '{}/{}/{}/{}.html'.format(OUTPUT_FOLDER, student_A,student_B, line_ref[1]['assignment'])
        file_pdf = '{}/{}/{}-{}-{}-{}.pdf'.format(OUTPUT_FOLDER, student_A, student_A, line_ref[1]['assignment'], line_ref[1]['percent'], student_B)
        
        if not os.path.exists(file_pdf):
            source_A = []
            with open(line_ref[0]['file_path'], 'rt') as in_file:
                for line in in_file:
                    source_A.append(line)

            source_B = []
            with open(line_ref[1]['file_path'], 'rt') as in_file:
                for line in in_file:
                    source_B.append(line)

            out_A = []
            out_B = []
            for key in line_ref[0]['lines']:
                lines_A = line_ref[0]['lines'][key]
                lines_B = line_ref[1]['lines'][key]
                for line_ind in range(lines_A['from']-1, lines_A['to']):
                    out_A.append(source_A[line_ind])
                out_A.append("="*50)

                for line_ind in range(lines_B['from']-1, lines_B['to']):
                    out_B.append(source_B[line_ind])
                out_B.append("="*50)

            if not os.path.exists(os.path.dirname(file_A)):
                try:
                    os.makedirs(os.path.dirname(file_A))
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            with open(file_A, 'w') as f:
                for item in out_A:
                    f.write("%s\n" % item)

            with open(file_B, 'w') as f:
                for item in out_B:
                    f.write("%s\n" % item)

            os.system("vimdiff {} {} -c 'colo morning' -c 'set diffopt+=context:99999' -c TOhtml -c 'w! {}' -c 'qa!'".format(file_A, file_B, file_diff))

            options = {
                'page-size': 'Legal',
                'orientation': 'Landscape',
                'margin-top': '0.25in',
                'margin-right': '0.25in',
                'margin-bottom': '0.25in',
                'margin-left': '0.25in',
                'encoding': "UTF-8",
                'no-outline': None
            }

            pdfkit.from_file(file_diff, file_pdf, options)
