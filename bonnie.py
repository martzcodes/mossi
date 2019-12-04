import zipfile
import os
import sys
import uuid
import json
import hashlib
from collections import defaultdict


# python bonnie.py assignment_2 ai/a2-anon ai/a2 spring-2019

ASSIGNMENT = sys.argv[1]
DIR_NAME = sys.argv[2]
OUTPUT_DIR = sys.argv[3]
SEMESTER = sys.argv[4]

ASSIGNMENT = "-{}-".format(ASSIGNMENT)

uuids = {}
if os.path.exists('{}/student-uuids.json'.format(OUTPUT_DIR)):
    with open('{}/student-uuids.json'.format(OUTPUT_DIR), 'r') as f:
        uuids = json.load(f)


count = 0
student = ''
student_count = 1
students = {}
student_checksums = {}

for path, dir_list, file_list in os.walk(DIR_NAME):
    for file_name in file_list:
        if file_name.endswith(".zip"):
            abs_file_path = os.path.join(path, file_name)
            name_raw = file_name.split(ASSIGNMENT)[0]
            last_name = name_raw.split("-")[-1]
            first_name = name_raw.split("-")[:-1]
            name_combined = "".join([last_name]+first_name)
            if name_combined not in students:
                students[name_combined] = []
            students[name_combined].append((path, file_name))

            if name_combined not in student_checksums:
                student_checksums[name_combined] = []
            student_checksum = hashlib.md5(os.path.join(path, file_name)).hexdigest() 
            student_checksums[name_combined].append(student_checksum)
            if student != name_combined:
                if student_count > 40:
                    # d = defaultdict(int)
                    # for i in student_checksums[name_combined]:
                    #     d[i] += 1
                    # max_same = max(d.iteritems(), key=lambda x: x[1])
                    # print(max_same)
                    # print("{}: {}... and submitted the same file {} times".format(student, student_count, max_same[1]))
                    print("{}: {}".format(student, student_count))
                student = name_combined
                student_count = 1
            else:
                student_count += 1


student = ''
for student_name, files in students.items():
    if student_name not in uuids:
        uuids[student_name] = str(uuid.uuid4().hex)
    student_uuid = uuids[student_name]
    process_files = [0]
    if len(files) > 3:
        process_files = [0, len(files)//2, len(files)-1]
    while len(process_files) < 3:
        process_files.append(len(files)-1)
    for sub, file_num in enumerate(process_files):
        path = files[file_num][0]
        file_name = files[file_num][1]
        abs_file_path = os.path.join(path, file_name)

        dt_raw = file_name.split(ASSIGNMENT)[1].split(".zip")[0]
        dt = "".join(dt_raw.split("-"))

        with zipfile.ZipFile(abs_file_path) as zf:  # open the zip file
            for target_file in zf.namelist():
                if target_file.endswith(".py"):
                    # generate the desired output name:
                    # studentname_1_datetime_assignmentpart.py

                    target_name = "{}/{}/sub{}/{}_{}_{}_{}".format(target_file.split(".")[0], SEMESTER, sub+1, student_uuid, file_num+1, dt, target_file)
                    target_path = os.path.join(OUTPUT_DIR, target_name)  # output path
                    # print("Target: {}".format(target_path))
                    if not os.path.exists(os.path.join(OUTPUT_DIR, target_file.split(".")[0], SEMESTER, "sub{}".format(sub+1))):
                        os.makedirs(os.path.join(OUTPUT_DIR, target_file.split(".")[0], SEMESTER, "sub{}".format(sub+1)))
                    with open(target_path, "wb") as f:  # open the output path for writing
                        f.write(zf.read(target_file))  # save the contents of the file in it
                    count += 1

with open('{}/student-uuids.json'.format(OUTPUT_DIR), 'w') as outfile:
    json.dump(uuids, outfile, indent=4, sort_keys=True)

print(count)