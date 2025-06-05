import csv
import doctest
from pathlib import Path
import re

from bs4 import BeautifulSoup


DATA_FOLDER = r'C:\Users\Tonechas\Dropbox\OngoingWork\GroupsInWorkshops'

NULL_GRADE = '-'

PARTICIPANT_CELLS = (
    'participant cell c0',
)

GIVEN_GRADE_CELLS = (
    'givengrade notnull cell c0 lastcol',
    'givengrade notnull cell c1 lastcol',
    'givengrade notnull cell c4',
)

RECEIVED_GRADE_CELLS = (
    'receivedgrade notnull cell c0',
    'receivedgrade notnull cell c2',
    'receivedgrade notnull cell c0 lastcol',
)

GRADING_GRADE_CELLS = (
    'gradinggrade cell c5 lastcol',
)


class User():
    """
    Represents a Moodle user, typically a student or a teacher.

    Parameters
    ----------
    last_name : str
        The user's last name.
    first_name : str
        The user's first name.
    group_ids : tuple of str, optional
        A list of IDs of the groups to which the user belongs.
        Defaults to None if not provided.

    Attributes
    ----------
    last_name : str
        The user's last name.
    first_name : str
        The user's first name.
    full_name : str
        The user's full name in the format "First Last".
    group_ids : tuple of str
        The IDs of the groups to which the user belongs.

    Examples
    --------
    >>> user1 = User('Doe', 'John', ('G1', 'Group 2.3'))
    >>> print(user1)
    User('John Doe')
    >>> user1.group_ids
    ('G1', 'Group 2.3')
    >>> user2 = User('Roe', 'Jane')
    >>> user2.full_name
    'Jane Roe'
    >>> user2.group_ids
    ()
    """
    def __init__(self, last_name, first_name, group_ids=None):
        self.last_name = last_name
        self.first_name = first_name
        self.full_name = f'{self.first_name} {self.last_name}'
        self.group_ids = group_ids if group_ids is not None else ()
    def __repr__(self):
        return f'{self.__class__.__name__}({self.full_name!r})'


class Group():
    """
    Represents a group of users identified by a unique group ID.

    Parameters
    ----------
    group_id : str
        A unique identifier for the group, such as 'A', 'C3.2'
        or 'Group 2.1'.
    members : tuple of User, optional
        A tuple of User instances.
        Defaults to an empty list if not provided.

    Attributes
    ----------
    group_id : str
        The identifier for the group.
    members : tuple of User
        The users who are members of the group. Those users whose
        groups_ids attribute does not contain the group_id won't
        be included in the group.

    Examples
    --------
    >>> g1 = Group('Group 1')
    >>> print(g1)
    Group('Group 1')
    >>> g1.members
    ()
    >>> user1 = User('Doe', 'Chris', 'A')
    >>> g2 = Group('A', (user1,))
    >>> g2.members
    (User('Chris Doe'),)
    >>> user2 = User('Smith', 'Sally', ['A', 'G3'])
    >>> g3 = Group('G3', [user1, user2])
    >>> g3.members
    (User('Sally Smith'),)
    """
    def __init__(self, group_id, members=None):
        self.group_id = group_id
        if members is None:
            self.members = ()
        else:
            self.members = tuple(
                member for member in members if group_id in member.group_ids
            )
    def __repr__(self):
        return f'{self.__class__.__name__}({self.group_id!r})'


class Course():
    def __init__(self, course_id, users, groups):
        self.course_id = course_id
        self.users = tuple(sorted(users, key=lambda x: x.last_name))
        self.groups = tuple(sorted(groups, key=lambda x: x.group_id))
    def __repr__(self):
        return f'{self.__class__.__name__}({self.course_id})'
    
    @classmethod
    def from_csv(cls, course_id):
        filename = f'courseid_{course_id}_participants.csv'
        csv_file = Path(DATA_FOLDER, filename)
        users = []
        groups = []
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for line in reader:
                if len(line) < 2:
                    print(f'Malformed user info: {line}')
                    continue  # Skip malformed rows
                first_name = line[0].strip()
                last_name = line[1].strip()
                try:
                    raw_ids = line[3].split(',')
                    group_ids = [group_id.strip() for group_id in raw_ids]
                except IndexError:
                    # User does not belong to any group
                    group_ids = []
                user = User(last_name, first_name, group_ids)
                users.append(user)
                for group_id in group_ids:
                    for group in groups:
                        if group.group_id == group_id:
                            group.members += (user,)
                            break
                    else:
                        groups.append(Group(group_id, [user]))
        return cls(course_id, tuple(users), tuple(groups))


class GradesReportParser():
    def __init__(self, filename):
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()
        self.soup = BeautifulSoup(html_content, 'lxml')

    @staticmethod
    def get_grade(grade_tag):
        text = grade_tag.get_text(strip=True)
        try:
            grade = float(text)
        except ValueError:
            # Decimal separator can be a ','
            grade = float(text.replace(',', '.'))
        return grade

    def extract_workshop_title(self):
        breadcrumb = self.soup.find('ol', class_='breadcrumb')
        last_li = breadcrumb.find_all('li')[-1]
        return last_li.get_text(strip=True)
    
    def extract_course_title(self):
        breadcrumb = self.soup.find('ol', class_='breadcrumb')
        for a_tag in breadcrumb.find_all('a'):
            if a_tag.has_attr('title'):
                return a_tag['title']

    def extract_course_id(self):
        """
        Extract the value of `courseId` from a BeautifulSoup object.
    
        Parameters
        ----------
        soup : bs4.BeatifulSoup
            The content of a workshop grades report (Moodle page).
    
        Returns
        -------
        int
            The course ID if found.
        """
        for script_tag in self.soup.find_all('script'):
            content = script_tag.string
            if not content or 'courseId' not in content:
                continue
            found = re.search(r'"courseId"\s*:\s*(\d+)', content)
            if found:
                return int(found.group(1))
        raise ValueError('Unable to extract "courseId".')

    def extract_group_ids(self):
        select_tag = self.soup.find('select', attrs={
            'class': ['custom-select', 'singleselect'],
            'name': 'group'
        })
        option_tags = select_tag.find_all('option')
        group_ids = set()
        for option in option_tags:
            # Discard default option: All participants
            if option['value'] != '0':
                group_ids.add(option.get_text(strip=True))
        return sorted(group_ids)

    def extract_rows(self):
        tables = self.soup.find_all('table')
        if not tables:
            raise ValueError('No <table> elements found in `soup`.')
        first_table = tables[0]
        tbody = first_table.find('tbody')
        if tbody is None:
            raise ValueError('No <tbody> found in the first table.')
        rows = []
        for tr in tbody.find_all('tr'):
            if tr.has_attr('class') and tr['class'] in ([], ['lastrow']):
                rows.append(tr)
        return rows

    def extract_participants(self):
        participants = []
        for row in self.extract_rows():
            td = row.find('td',class_=lambda x: x in PARTICIPANT_CELLS)
            if td:
                participants.append(td.contents[-1].text)
        return participants


    def extract_grades(self):
        grades = dict()
        for row in self.extract_rows():
            td_part = row.find('td', class_=lambda x: x in PARTICIPANT_CELLS)
            if td_part:
                participant = td_part.contents[-1].text
                grades[participant] = {
                    'received': dict(),
                    'given': dict(),
                    'assessment': NULL_GRADE,
                }        
            td_rec = row.find('td', class_=lambda x: x in RECEIVED_GRADE_CELLS)
            if td_rec:
                fullname_tag = td_rec.find('span', class_='fullname')
                grader = fullname_tag.get_text(strip=True)
                grade_tag = td_rec.find('span', class_='grade')
                grade = self.get_grade(grade_tag)
                grades[participant]['received'][grader] = grade
            td_given = row.find('td', class_=lambda x: x in GIVEN_GRADE_CELLS)
            if td_given:
                fullname_tag = td_given.find('span', class_='fullname')
                gradee = fullname_tag.get_text(strip=True)
                grade_tag = td_given.find('span', class_='grade')
                grade = self.get_grade(grade_tag)
                grades[participant]['given'][gradee] = grade
            td_grad = row.find('td', class_=lambda x: x in GRADING_GRADE_CELLS)
            if td_grad:
                if td_grad.get_text() != NULL_GRADE:
                    grade = self.get_grade(td_grad)
                    grades[participant]['assessment'] = grade
        # Sanity check
        for gradee in grades:
            for grader in grades[gradee]['received']:
                gradee_from_grader = grades[gradee]['received'][grader]
                grader_to_gradee = grades[grader]['given'][gradee]
                if gradee_from_grader != grader_to_gradee:
                    raise ValueError('Error parsing grades')
        return grades


class Workshop():
    def __init__(self, filename):
        self.parser = GradesReportParser(filename)
        self.workshop_title = self.parser.extract_workshop_title()
        self.course = self.get_course()
        
        self.group_ids = self.parser.extract_group_ids()
        self.grades_from_report = self.parser.extract_grades()
        self.grades = self.compute_grades()

#        self.groups = self.get_groups()
#        self.participants = self.get_participants()

    def get_course(self):
        course_id = self.parser.extract_course_id()
        #course_title = self.parser.extract_course_title()
        return Course.from_csv(course_id)

        
    def get_workshop_groups(self):
            # course = Course.from_csv(self.course_id)
            # users = course.users
            # groups = []
            # for group_id in self.group_ids:
            #     members = []
            #     for user in users:
            #         if group_id in user.group_ids:
            #             members.append(user)
            #     group = Group(group_id, members)
            #     groups.append(group)
            groups = [group for group in self.course.groups
                      if group.group_id in self.group_ids]
            return groups

    def compute_grades(self):
        grades = dict()
        groups = self.get_workshop_groups()
        for group in groups:
            full_names = [member.full_name for member in group.members]
            received = []
            for full_name in full_names:
                grades[full_name] = dict()
                mapping = self.grades_from_report[full_name]
                received.extend(mapping['received'].values())
            if received:
                group_grade = sum(received)/len(received)
            else:
                group_grade = NULL_GRADE
            for full_name in full_names:
                grades[full_name]['submission'] = group_grade
        for full_name in grades:
            submission = grades[full_name]['submission']
            assessment = self.grades_from_report[full_name]['assessment']
            submission = submission if submission is not NULL_GRADE else 0
            assessment = assessment if assessment is not NULL_GRADE else 0
            grades[full_name]['overall'] = submission + assessment
        return grades
    
    def display_grades(self):
        print('NAME                          Submission  Assessment  Overall')
        print('-------------------------------------------------------------')
        for full_name in self.grades:
            submission = self.grades[full_name]['submission']
            assessment = self.grades_from_report[full_name]['assessment']
            if assessment == NULL_GRADE:
                assessment = 0
            overall = self.grades[full_name]['overall']
            print(f'{full_name:30}{submission:10.2f}'
                  f'{assessment:10.2f}{overall:11.2f}')

    def save_grades(self, filename):
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['Name', 'Submission', 'Assessment', 'Overall'])
            for full_name in self.grades:
                submission = self.grades[full_name]['submission']
                assessment = self.grades_from_report[full_name]['assessment']
                if assessment == NULL_GRADE:
                    assessment = 0
                overall = self.grades[full_name]['overall']
                writer.writerow([full_name, f'{submission:4.2f}',
                                 f'{assessment:4.2f}', f'{overall:4.2f}'])



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


#geo2 = CourseParticipants.from_csv(22862)
#eg = CourseParticipants.from_csv(23252)

if __name__ == '__main__':
    doctest.testmod()

html_file = Path(DATA_FOLDER, 'geo2-practica4.htm')
csv_file = Path(DATA_FOLDER, 'geo2-practica4.csv')

geo2 = Course.from_csv(22862)
p4 = Workshop(html_file)
p4.save_grades(csv_file)

#wd = WorkshopReport('eg-shaft-support.htm')


        
