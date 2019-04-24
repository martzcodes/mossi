import os
import sys
from shutil import copyfile
import json

last_semester_dir = sys.argv[1]
uuid_dir = sys.argv[2]

uuids = {}
if os.path.exists('{}/student-uuids.json'.format(uuid_dir)):
    with open('{}/student-uuids.json'.format(uuid_dir), 'r') as f:
        uuids = json.load(f)

count = 0
for path, dir_list, file_list in os.walk(last_semester_dir):
   for file_name in file_list:
       if file_name.endswith(".py") and len(file_name.split("_")) == 4:
            abs_file_path = os.path.join(path, file_name)
            name_parts = file_name.split("_")[1].split(" ")
            reordered_name = name_parts
            # reordered_name = []
            # for j in range(1,len(name_parts)):
            #     reordered_name.append(name_parts[j])
            # reordered_name.append(name_parts[0])
            student_name = "".join(reordered_name).lower()
            if student_name in uuids:
                student_name = uuids[student_name]
            new_path = os.path.join(path, "{}_1_1_{}_{}".format(student_name, file_name.split("_")[2], file_name.split("_")[3]))
            copyfile(abs_file_path, new_path)