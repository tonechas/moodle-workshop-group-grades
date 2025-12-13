from pathlib import Path

from moodle_models import Course, Workshop
#from util import DataFolderManager
from util import select_html_file
from moodle_models import SEPARATOR

#GRADE_MIN = 0
#GRADE_MAX = 100

# course_id = 22862
# workshop_id = 'geo2-practica4'
# config_file = 'config.ini'

html_input_file = select_html_file(
    r'C:\Users\Tonechas\Dropbox\OngoingWork\GroupsInWorkshops\data'
)

data_folder = html_input_file.parent
filename = html_input_file.stem
extension = html_input_file.suffix

csv_output_file = data_folder.joinpath(f'{filename}.csv')


course_id, workshop_id = filename.split(SEPARATOR)

print(f'Data folder selected:\n    {data_folder}')
print(f'Course ID:\n    {course_id}')
print(f'Workshop ID:\n    {workshop_id}')

p4 = Workshop(html_input_file)
geo2 = p4.course
p4.display_grades()
p4.save_grades(csv_output_file)

# dfm = DataFolderManager(
#     config_file=config_file,
#     section="paths",
#     key="data_folder",
# )

# data_folder = dfm.get_data_folder()    
# geo2 = Course.from_participants_csv(course_id, data_folder)

