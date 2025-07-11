import csv
import doctest
from pathlib import Path
import unicodedata

from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np

import grades_report_parser as grp

# !!! Fix this
DATA_FOLDER = r'C:\Users\Tonechas\Dropbox\OngoingWork\GroupsInWorkshops'

GRADE_MIN = 0
GRADE_MAX = 100


def normalize(text):
    """
    Remove accents from a string and convert to lowercase.

    Helper function for sorting strings in a way that ignores
    diacritical marks (accents) and case.

    Parameters
    ----------
    text : str
        The input string to normalize.

    Returns
    -------
    str
        A normalized version of the input string without accents, 
        converted to lowercase.

    Examples
    --------
    >>> normalize('Ángel Fernández Peña')
    'angel fernandez pena'
    
    >>> names = ['ángel', 'Marta', 'Óscar', 'María', 'Elena', 'ana']
    >>> sorted(names)  # Unicode order (not what we want)
    ['Elena', 'Marta', 'María', 'ana', 'Óscar', 'ángel']
    >>> sorted(names, key=normalize)  # Normalized order
    ['ana', 'ángel', 'Elena', 'María', 'Marta', 'Óscar']
    """
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).lower()


class User():
    """
    Represents a Moodle user, typically a student or a teacher.

    Parameters
    ----------
    last_name : str
        The user's last name.
    first_name : str
        The user's first name.
    group_ids : str, list of str, or None, optional
        An ID or a list of IDs of the group(s) to which the user belongs.
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
        Group IDs associated with the user. Always stored as a tuple, 
        regardless of whether a single string, a list of strings, or
        `None` was passed at initialization.

    Examples
    --------
    >>> user1 = User('Doe', 'John', 'johny@example.com', ['G1', 'Group 2.3'])
    >>> print(user1)
    User('John Doe')
    >>> user1.email
    'johny@example.com'
    >>> user1.group_ids
    ('G1', 'Group 2.3')
    
    >>> user2 = User('Roe', 'Jane', 'jane2005@fakemail.net')
    >>> user2.full_name
    'Jane Roe'
    >>> user2.group_ids
    ()

    >>> user3 = User('Smith', 'Alice', 'alice2008@fakemail.net', 'A2')
    >>> user3.group_ids
    ('A2',)

    >>> user4 = User('Brown', 'Charlie', 'charlie@nomail.com', None)
    >>> user4.group_ids
    ()
    """
    def __init__(self, last_name, first_name, email, group_ids=None):
        self.last_name = last_name
        self.first_name = first_name
        self.full_name = f'{self.first_name} {self.last_name}'
        self.email = email
        self.group_ids = group_ids
    
    @property
    def group_ids(self):
        return self._group_ids

    @group_ids.setter
    def group_ids(self, ids):
        if ids is None:
            self._group_ids = ()
        elif isinstance(ids, str):
            self._group_ids = (ids,)
        elif isinstance(ids, list):
            self._group_ids = tuple(ids)
        else:
            raise ValueError('Invalid groups IDs')

    def __repr__(self):
        return f'{self.__class__.__name__}({self.full_name!r})'

    def __lt__(self, other):
        """
        Compare two User instances for sorting purposes.
    
        Users are compared by their last names and first names in a
        case-insensitive and accent-insensitive manner using the
        `normalize()` helper function.
    
        Parameters
        ----------
        other : User
            Another instance of User to compare against.
    
        Returns
        -------
        bool
            True if the current user should come before `other`
            in sorted order, False otherwise.
    
        Examples
        --------
        >>> user1 = User('Johnson', 'Bob', 'bobby@example.com')
        >>> user2 = User('Smith', 'Alice', 'alice2008@fakemail.net')
        >>> user1 < user2
        True
        
        >>> user3 = User('Pérez', 'Mario', 'mario@example.com')
        >>> user4 = User('Pérez', 'María', 'maria@fakemail.net')
        >>> user3 < user4
        False
        """
        tup_self = (normalize(self.last_name), normalize(self.first_name))
        tup_other = (normalize(other.last_name), normalize(other.first_name))
        return tup_self < tup_other


class Group():
    """
    Represents a group of users identified by a unique group ID.

    Parameters
    ----------
    group_id : str
        A unique identifier for the group, such as 'A', 'C3.2'
        or 'Group 2_1'.
    members : list of User, optional
        A list of User instances.
        Defaults to an empty tuple if not provided.

    Attributes
    ----------
    group_id : str
        The identifier for the group.
    members : tuple of User
        The users who are members of the group. Those users whose
        groups_ids attribute does not contain the group_id won't
        be included in this tuple.

    Examples
    --------
    >>> group1 = Group('Group 1')
    >>> print(group1)
    Group('Group 1')
    >>> group1.group_id
    'Group 1'
    >>> group1.members
    ()
    
    >>> user1 = User('Doe', 'Chris', 'chris@example.com', 'A')
    >>> group2 = Group('A', (user1,))
    >>> group2.members
    (User('Chris Doe'),)
    
    >>> user2 = User('Smith', 'Sally', 'sally205@fakemail.net', ['A', 'G3'])
    >>> group3 = Group('G3', [user1, user2])
    >>> group3.members
    (User('Sally Smith'),)

    >>> group4 = Group('A', [user1, user2])
    >>> group4.members
    (User('Chris Doe'), User('Sally Smith'))
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
    """
    Represents a Moodle course with users and group assignments.

    This class models the participant list of a Moodle course,
    including all users and their group affiliations. It verifies
    that group membership matches the users' declared group IDs.

    Parameters
    ----------
    course_id : int
        The unique identifier assigned to the course by Moodle.
    users : list of User
        A list of User instances enrolled in the course.
    groups : list of Group
        A list of Group instances associated with the course.

    Attributes
    ----------
    course_id : int
        The Moodle-assigned course identifier.
    users : tuple of User
        All users enrolled in the course, sorted by last name.
    groups : tuple of Group
        All groups in the course, sorted by group ID.

    Raises
    ------
    ValueError
        If any group's members do not match the users who list that
        group's ID in their `group_ids` attribute.

    Class Methods
    -------------
    from_csv(course_id)
        Constructs a Course instance from a Moodle CSV file named
        `courseid_<course_id>_participants.csv`. The file must have
        four columns: first name, last name, email, and groups. Group
        names must be comma-separated.

    Examples
    --------
    >>> path = Path('.', 'courseid_12345_participants.csv')
    >>> with open(path, 'w') as f:
    ...     print(r'"First name",Surname,"Email address",Groups', file=f)
    ...     print(r'Sally,Smith,sally@gmail.com,"A, G1_2"', file=f)
    ...     print(r'Joe,Bloggs,joe@yahoo.com,"B, G1_1"', file=f)
    ...     print(r'Jane,Roe,jenny@hotmail.com,"B, G1_2"', file=f)
    ...     print(r'John,Doe,johny@example.com,"A, G1_1"', file=f)
    ...
    >>> course = Course.from_csv(12345)
    >>> for user in course.users:
    ...     print(user)
    ...
    User('Joe Bloggs')
    User('John Doe')
    User('Jane Roe')
    User('Sally Smith')
    >>> type(course.users)
    <class 'tuple'>
    >>> course.groups
    (Group('A'), Group('B'), Group('G1_1'), Group('G1_2'))
    """
    def __init__(self, course_id, users, groups):
        self.course_id = course_id
        self.users = tuple(sorted(users))
        self.groups = tuple(sorted(groups, key=lambda x: x.group_id))
        for group in self.groups:
            group_users = []
            for user in users:
                if group.group_id in user.group_ids:
                    group_users.append(user)
            if [user for user in group_users if user not in group.members]:
                raise ValueError(f'Group {group} is malformed')

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
                email = line[2].strip()
                try:
                    raw_ids = line[3].split(',')
                    group_ids = [group_id.strip() for group_id in raw_ids]
                except IndexError:
                    # User does not belong to any group
                    group_ids = []
                user = User(last_name, first_name, email, group_ids)
                users.append(user)
                for group_id in group_ids:
                    for group in groups:
                        if group.group_id == group_id:
                            group.members += (user,)
                            break
                    else:
                        groups.append(Group(group_id, [user]))
        return cls(course_id, users, groups)


class Workshop():
    """
    Represents a Moodle workshop and manages group-based grading.

    This class parses a Moodle workshop HTML report to extract 
    the course ID, group identifiers, and user grades. It links 
    report data with the corresponding course participants 
    loaded from a CSV file, computes group submission scores, 
    and combines them with assessment grades.

    Parameters
    ----------
    filename : str
        Path to the HTML report file exported from Moodle.

    Attributes
    ----------
    soup : bs4.BeautifulSoup
        Parsed HTML content of the workshop report.
    workshop_title : str
        Title of the workshop, as shown in the report.
    course : Course
        Course instance with users and group membership.
    group_ids : list of str
        List of group IDs found in the HTML report.
    grades_from_report : dict of str to dict
        Raw grading data extracted from the report. Each key is a 
        user's full name; each value is a dictionary with keys 
        'submitted', 'received', 'given', 'submission' and 'grading'.
    grades : dict of str to dict
        Computed grades for each user. Each key is a user's full 
        name; each value is a dictionary with keys 'submission' 
        and 'overall', representing the group submission score 
        and the total grade (submission + assessment).
    """
    def __init__(self, filename):
        self.soup = self.get_soup(filename)
        self.workshop_title = grp.extract_workshop_title(self.soup)
        self.course = self.get_course()
        self.group_ids = grp.extract_group_ids(self.soup)
        self.grades_from_report = grp.extract_grades(self.soup)
        self.grades = self.compute_grades()


    def get_soup(self, filename):
        """
        Read the specified HTML file and parse its content using 
        BeautifulSoup with the 'lxml' parser.
    
        Parameters
        ----------
        filename : str
            Path to the HTML file exported from a Moodle workshop 
            grades report.
        
        Returns
        -------
        bs4.BeautifulSoup
            Parsed HTML content of the grades report, used
            internally for extracting information.
        """
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return BeautifulSoup(html_content, 'lxml')
        
    def get_course(self):
        """
        Load course participant data based on the course ID.

        This method extracts the course ID from the workshop's HTML
        report and uses it to instantiate a `Course` object by reading
        the corresponding CSV file. The CSV file is expected to be
        named `courseid_<id>_participants.csv`.

        Returns
        -------
        course_obj : Course
            A `Course` object containing the list of users and groups
            associated with the workshop's course.

        See Also
        --------
        Course.from_csv : Method that reads and parses the CSV
        participant list.
        """
        course_id = grp.extract_course_id(self.soup)
        #course_title = self.parser.extract_course_title()
        course_obj = Course.from_csv(course_id)
        return course_obj

        
    def get_workshop_groups(self):
        """
        Return the list of groups involved in the current workshop.
    
        Filters the course's groups to include only those whose 
        group IDs appear in the HTML report. These are the groups 
        that actively participated in the workshop.
    
        Returns
        -------
        groups : list of Group
            Groups matched by ID as listed in the workshop report.
        """
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
                group_grade = grp.NULL_GRADE
            for full_name in full_names:
                if self.grades_from_report[full_name]['submitted']:
                    grades[full_name]['submission'] = group_grade
                else:
                    grades[full_name]['submission'] = 0
        for full_name in grades:
            submission = grades[full_name]['submission']
            assessment = self.grades_from_report[full_name]['grading']
            submission = submission if submission is not grp.NULL_GRADE else 0
            assessment = assessment if assessment is not grp.NULL_GRADE else 0
            grades[full_name]['overall'] = submission + assessment
        return grades
    
    def display_grades(self):
        print('Name                          Submission  Assessment  Overall')
        print('-------------------------------------------------------------')
        for user in sorted(p4.course.users):
            full_name = user.full_name
            if full_name in self.grades:
                submission = self.grades[full_name]['submission']
                assessment = self.grades_from_report[full_name]['grading']
                if assessment == grp.NULL_GRADE:
                    assessment = 0
                overall = self.grades[full_name]['overall']
                print(f'{full_name:30}{submission:10.2f}'
                      f'{assessment:10.2f}{overall:11.2f}')

    def save_grades(self, filename):
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['Name', 'Submission', 'Assessment', 'Overall'])
            
            for user in sorted(p4.course.users):
                full_name = user.full_name
                if full_name in self.grades.keys():
                    submission = self.grades[full_name]['submission']
                    assessment = self.grades_from_report[full_name]['grading']
                    if assessment == grp.NULL_GRADE:
                        assessment = 0
                    overall = self.grades[full_name]['overall']
                    writer.writerow([full_name, f'{submission:4.2f}',
                                     f'{assessment:4.2f}', f'{overall:4.2f}'])


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


if __name__ == '__main__':
    doctest.testmod()

html_file = Path(DATA_FOLDER, 'geo2-practica4.htm')
csv_file = Path(DATA_FOLDER, 'geo2-practica4.csv')

geo2 = Course.from_csv(22862)
p4 = Workshop(html_file)
#%%
p4.save_grades(csv_file)
p4.display_grades()

# !!!
len(p4.grades) == len(p4.course.users)

per_user = []
per_group = []

for user in p4.grades_from_report:
    if p4.grades_from_report[user]['submitted']:
        raw_grade = p4.grades_from_report[user]['submission']
        grade = 0 if raw_grade == grp.NULL_GRADE else raw_grade
        per_user.append(grade)
        per_group.append(p4.grades[user]['submission'])

per_user = np.array(per_user)
per_group = np.array(per_group)
diff_group_user = per_group - per_user

PLOT_DIFF = True

bins_diff = np.linspace(-GRADE_MAX/5, GRADE_MAX/5, 21)
bins_grade = np.linspace(GRADE_MIN, GRADE_MAX, 21)
bins_grade[-1] += 1e-6  # To include 100 in the last bin

hist_users, _ = np.histogram(per_user, bins=bins_grade, density=False)
hist_groups, _ = np.histogram(per_group, bins=bins_grade, density=False)
hist_diff, _ = np.histogram(diff_group_user, bins=bins_diff, density=False)

bin_diff_width = bins_diff[1] - bins_diff[0]
bin_diff_centers = bins_diff[:-1] + bin_diff_width / 2

bin_grade_width = bins_grade[1] - bins_grade[0]
bin_grade_centers = bins_grade[:-1] + bin_grade_width / 2

# Ancho de las barras para cada conjunto (dividir el bin en 2)
bar_diff_width = bin_diff_width / 2
bar_grade_width = bin_grade_width / 2

# Graficar: barras pegadas una a otra para cada bin
plt.ylabel('Frequency')
if PLOT_DIFF:
    plt.bar(bin_diff_centers - bar_diff_width / 2,
            hist_diff, width=bar_diff_width, alpha=0.7)
    plt.xlabel('Group grade - Submission grade')
    plt.title('Histogram of differences between group and submission grades')
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
print(f'{diff_group_user.mean() = :.2f}')
print(f'{diff_group_user.std() = :.2f}')

#eg = Course.from_csv(23252)
#html_file = Path(DATA_FOLDER, 'eg-shaft-support.htm')
#csv_file = Path(DATA_FOLDER, 'eg-shatft-support.csv')

