from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from moodle_models import Course, Workshop
import moodle_workshop_report_parser as mwrp
from util import DataFolderManager


GRADE_MIN = 0
GRADE_MAX = 100


dfm = DataFolderManager(
    config_file="config.ini",
    section="paths",
    key="data_folder",
)

# !!! Probar a cambiar este directorio en config.ini
#data_folder = r'C:\Users\Tonechas\Dropbox\OngoingWork\GroupsInWorkshops'
data_folder = dfm.get_data_folder()
print(f"Data folder selected: {data_folder}")
    

html_file = Path(data_folder, 'geo2-practica4.htm')
csv_file = Path(data_folder, 'geo2-practica4.csv')
    
geo2 = Course.from_participants_csv(22862, data_folder)
p4 = Workshop(html_file)

p4.display_grades()
p4.save_grades(csv_file)


# !!! Cambiar instrucciones en README.md

# !!! "First name","Last name","ID number","Email address",Groups

#  !!! ¿?Qué pasa con los que no tienen ID number?

    # !!! Add sanity tests
    # def get_participants(self):
    #     full_names = self.soup.extract_participants()
    #     if len(full_names) != len(set(full_names)):
    #         raise ValueError('Duplicate names detected in participant list.')
    #     course_participants = CourseParticipants.from_csv(self.course_id)
    #     users = course_participants.users
    #     participants = [user for user in users if user.full_name in full_names]
    #     if set(obj.full_name for obj in participants) != set(full_names):
    #         raise ValueError('Error parsing participant names')
    #     return sorted(participants, key=lambda x: x.last_name)
        


    # def make_groups(self):
    #     group_ids = set()
    #     for user in self.users:
    #         group_ids |= set(user.groups)
    #     groups = []
    #     for group_id in sorted(group_ids):
    #         members = []
    #         for user in self.users:
    #             if group_id in user.groups:
    #                 members.append(user)
    #         groups.append(Group(group_id, members))
    #     return groups

# !!! Usar conjuntos en los sanity checks
#%%
MYFLAG = True

if MYFLAG:

# !!! Convertir esto en un método  
    per_user = []
    per_group = []
    
    for full_name, mapping in p4.grades_from_report.items():
        if mapping['submitted']:
            raw_grade = mapping['submission']
            grade = 0 if raw_grade == mwrp.NULL_GRADE else raw_grade
            per_user.append(grade)
            per_group.append(p4.grades[full_name]['submission'])
    
    per_user = np.array(per_user)
    per_group = np.array(per_group)
    diff_user_group = per_user - per_group

if MYFLAG:
    
    PLOT_DIFF = True
    NUM_BINS = 11
    FRACTION_OF_GRADE_MAX = 8
    bins_diff = np.linspace(-GRADE_MAX/FRACTION_OF_GRADE_MAX,
                            GRADE_MAX/FRACTION_OF_GRADE_MAX,
                            NUM_BINS + 1)
    bins_grade = np.linspace(GRADE_MIN, GRADE_MAX, NUM_BINS + 1)
    bins_grade[-1] += 1e-6  # To include 100 in the last bin
    
    hist_users, _ = np.histogram(per_user, bins=bins_grade, density=False)
    hist_groups, _ = np.histogram(per_group, bins=bins_grade, density=False)
    hist_diff, bin_cen_diff = np.histogram(diff_user_group, bins=bins_diff, density=False)
    
    with open('histo-diff-user-group.txt', 'w') as fout:
        print('label;freq', file=fout)
        for label, freq in zip(bin_cen_diff, hist_diff):
            print(f'{label:.2f};{freq}', file=fout)
    
    bin_diff_width = bins_diff[1] - bins_diff[0]
    bin_diff_centers = bins_diff[:-1] + bin_diff_width/2
    
    bin_grade_width = bins_grade[1] - bins_grade[0]
    bin_grade_centers = bins_grade[:-1] + bin_grade_width/2
    
    # Ancho de las barras para cada conjunto (dividir el bin en 2)
    bar_diff_width = bin_diff_width / 2
    bar_grade_width = bin_grade_width / 2
    
    # Graficar: barras pegadas una a otra para cada bin
    plt.ylabel('Frequency')
    if PLOT_DIFF:
        plt.bar(bin_diff_centers - bar_diff_width / 2,
                hist_diff, width=bar_diff_width, alpha=0.7)
        plt.xlabel('Individual grade - Group grade')
        plt.title('Histogram of differences between indiviadual and group grades')
    else:
        plt.bar(bin_grade_centers - bar_grade_width / 2,
                hist_users, width=bar_grade_width, alpha=0.7, label='Per user')
        plt.bar(bin_grade_centers + bar_grade_width / 2, 
                hist_groups, width=bar_grade_width, alpha=0.7, label='Per group')
        plt.xlabel('Submission grade')
        plt.title('Histograms of submission grades per user and per group')
        plt.legend()
        
    
    
    plt.grid(True)
    plt.show()
    
    print(f'{per_user.mean() = :.2f}')
    print(f'{per_user.std() = :.2f}')
    print(f'{per_group.mean() = :.2f}')
    print(f'{per_group.std() = :.2f}')
    print(f'{diff_user_group.mean() = :.2f}')
    print(f'{diff_user_group.std() = :.2f}')
    
    #eg = Course.from_csv(23252)
    #html_file = Path(data_folder, 'eg-shaft-support.htm')
    #csv_file = Path(data_folder, 'eg-shatft-support.csv')
#%%
# !!! Check this cell
# with open('boxplot.txt', 'w') as fbox, open('grade-of-groups.txt', 'w') as fgroup:
#     print('group;grade', file=fbox)
#     print('group;grade', file=fgroup)
#     for group in geo2.groups[6:-1]:
#         value_saved = False
#         group_id = group.group_id.split()[-1].replace('_', '.')
#         for member in group.members:
#             full_name = member.full_name
#             if p4.grades_from_report[full_name]['submitted']:
#                 individual_grade = p4.grades_from_report[full_name]['submission']
#                 print(f'{group_id};{individual_grade:5.2f}', file=fbox)
#                 group_grade = p4.grades[full_name]['submission']
#                 if not value_saved:
#                     print(f'{group_id};{group_grade:5.2f}', file=fgroup)
#                     value_saved = True
        
