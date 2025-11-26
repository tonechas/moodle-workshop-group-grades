from pathlib import Path

from moodle_models import Course, Workshop
from util import DataFolderManager


GRADE_MIN = 0
GRADE_MAX = 100

course_id = 22862
workshop_id = 'geo2-practica4'

dfm = DataFolderManager(
    config_file="config.ini",
    section="paths",
    key="data_folder",
)

data_folder = dfm.get_data_folder()
print(f"Data folder selected: {data_folder}")

html_file = Path(data_folder, f'{workshop_id}.html')
csv_file = Path(data_folder, 'f{workshop_id}.csv')
    
geo2 = Course.from_participants_csv(course_id, data_folder)
p4 = Workshop(html_file)

p4.display_grades()
p4.save_grades(csv_file)
