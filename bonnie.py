import zipfile
import os
import sys

assignment = sys.argv[1]
dir_name = sys.argv[2]
output_dir = sys.argv[3]

assignment = "-{}-".format(assignment)

count = 0
student = ''
student_count = 1
students = {}

for path, dir_list, file_list in os.walk(dir_name):
    for file_name in file_list:
        if file_name.endswith(".zip"):
            abs_file_path = os.path.join(path, file_name)
            name_raw = file_name.split(assignment)[0]
            last_name = name_raw.split("-")[-1]
            first_name = name_raw.split("-")[:-1]
            name_combined = "".join([last_name]+first_name)
            if name_combined not in students:
                students[name_combined] = []
            students[name_combined].append((path, file_name))
            if student != name_combined:
                if student_count > 40:
                    print("{}: {}".format(student, student_count))
                student = name_combined
                student_count = 1
            else:
                student_count += 1


student = ''
student_count = 1
for student_name, files in students.items():
    process_files = files
    if len(files) > 3:
        process_files = [files[0], files[len(files)//2], files[-1]]
    while len(process_files) < 3:
        process_files.append(process_files[-1])
    for sub, ele in enumerate(process_files):
        path = ele[0]
        file_name = ele[1]
        abs_file_path = os.path.join(path, file_name)
        name_raw = file_name.split(assignment)[0]
        last_name = name_raw.split("-")[-1]
        first_name = name_raw.split("-")[:-1]
        name_combined = "".join([last_name]+first_name)
        if student != name_combined:
            if student_count > 40:
                print("{}: {}".format(student, student_count))
            student = name_combined
            student_count = 1
        else:
            student_count += 1

        dt_raw = file_name.split(assignment)[1].split(".zip")[0]
        dt = "".join(dt_raw.split("-"))

        with zipfile.ZipFile(abs_file_path) as zf:  # open the zip file
            for target_file in zf.namelist():
                if target_file.endswith(".py"):
                    # generate the desired output name:
                    # studentname_1_datetime_assignmentpart.py

                    target_name = "{}/sub{}/{}_{}_{}_{}".format(target_file.split(".")[0], sub+1, name_combined, student_count, dt, target_file)
                    target_path = os.path.join(output_dir, target_name)  # output path
                    # print("Target: {}".format(target_path))
                    if not os.path.exists(os.path.join(output_dir, target_file.split(".")[0], "sub{}".format(sub+1))):
                        os.makedirs(os.path.join(output_dir, target_file.split(".")[0], "sub{}".format(sub+1)))
                    with open(target_path, "wb") as f:  # open the output path for writing
                        f.write(zf.read(target_file))  # save the contents of the file in it
                    count += 1
print(count)