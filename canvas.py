import os
import sys
from shutil import copyfile

assignment = sys.argv[1]
dir_name = "{}/{}".format(assignment, sys.argv[2])
output_dir = "{}/{}".format(assignment, sys.argv[3])

count = 0
for path, dir_list, file_list in os.walk(dir_name):
   for file_name in file_list:
       if file_name.endswith(".py"):
            abs_file_path = os.path.join(path, file_name)
            cleaned_file_name = file_name.split("-")[0]
            if not cleaned_file_name.endswith('.py'):
                cleaned_file_name += '.py'
            folder_name = file_name.split("-")[0].split("_")[-1].split(".py")[0]
            new_path = os.path.join(output_dir, folder_name, 'sub4', cleaned_file_name)
            if not os.path.exists(os.path.join(output_dir, folder_name, 'sub4')):
                os.makedirs(os.path.join(output_dir, folder_name, 'sub4'))
            copyfile(abs_file_path, new_path)