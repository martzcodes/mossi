import sys
from mossi import Mossi

# moss user id
userid = sys.argv[1]

# folders should be organized as assignment/<assignment_file>/semester-year/sub#/<file>, etc
dir_name = sys.argv[2]

OUTPUT_DIR = sys.argv[3]

# current semester based on file naming convention
curr_semester = sys.argv[4]

base_file = None
if len(sys.argv) == 6:
    base_file = sys.argv[5]


mossi = Mossi(userid, dir_name, OUTPUT_DIR, curr_semester, base_file)

if not mossi.pre_process():
    print("Pre-Process Failed")
    sys.exit()
if not mossi.moss():
    print("MOSS Failed")
    sys.exit()
if not mossi.post_process():
    print("Post-Process Failed")
    sys.exit()
if not mossi.output():
    print("Output Failed")
    sys.exit()

print("Complete")