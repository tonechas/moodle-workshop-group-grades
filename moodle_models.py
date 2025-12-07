from collections import defaultdict
import csv
import doctest
from pathlib import Path

from bs4 import BeautifulSoup

import moodle_workshop_report_parser as mwrp
from util import normalize


class User():
    """
    Represents a Moodle user, typically a student or a teacher.

    Parameters
    ----------
    first_name : str
        The user's first name.
    last_name : str
        The user's last name.
    id_number : int
        The user's ID number in the Moodle database.
    group_ids : str, list of str, tuple or None, optional
        An ID or a list of IDs of the group(s) to which the user belongs.
        Defaults to `None` if not provided.

    Attributes
    ----------
    first_name : str
        The user's first name.
    last_name : str
        The user's last name.
    id_number : int
        The user's ID number in the Moodle database.
    full_name : str
        The user's full name in the format "First Last".
    group_ids : tuple of str
        Group IDs associated with the user. Always stored as a tuple, 
        regardless of whether a single string, a list of strings, or
        `None` was passed at initialization.

    Examples
    --------
    >>> user1 = User('John', 'Doe', 123456, 'johny@nomail.com', ['G1', 'A'])
    >>> user1.full_name
    'John Doe'
    >>> user1.id_number
    123456
    >>> user1.email
    'johny@nomail.com'
    >>> user1.group_ids
    ('A', 'G1')
    >>> print(user1)
    User('John Doe', 123456)
    
    >>> user2 = User('Alice', 'Smith', 345678, 'alice08@example.net', 'A2')
    >>> user2.group_ids
    ('A2',)

    >>> user3 = User('Jane', 'Roe', 234567, 'jane2005@fakemail.net')
    >>> user3.full_name
    'Jane Roe'
    >>> user3.group_ids
    ()

    >>> user4 = User('James', 'Brown', 4567890, 'jim@example.com', None)
    >>> user4.group_ids
    ()
    
    """
    def __init__(
            self,
            first_name,
            last_name,
            id_number,
            email,
            group_ids=None,
        ):
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = f'{self.first_name} {self.last_name}'
        self.id_number = id_number
        self.email = email
        self.group_ids = group_ids
    
    
    @property
    def group_ids(self):
        return self._group_ids


    @group_ids.setter
    def group_ids(self, ids):
        if ids is None or ids == '':
            self._group_ids = ()
        elif isinstance(ids, str):
            self._group_ids = (ids,)
        elif isinstance(ids, (list, tuple)):
            valid_ids = set(str(id_) for id_ in ids if id_ not in (['', None]))
            self._group_ids = tuple(sorted(valid_ids, key=normalize))
        else:
            raise ValueError('Invalid group IDs')


    def __repr__(self):
        class_ = self.__class__.__name__
        full_name = self.full_name
        id_number = self.id_number
        return f'{class_}({full_name!r}, {id_number})'


    def __lt__(self, other):
        """
        Compare two User instances for sorting purposes.
    
        Users are compared by their last names and first names in a
        case-insensitive and accent-insensitive manner using the
        `normalize()` helper function. If the normalized last name
        and first name are identical for both users, the comparison
        uses `id_number` as a tiebreaker to guarantee consistent
        ordering.
    
        Parameters
        ----------
        other : User
            Another instance of User to compare against.
    
        Returns
        -------
        bool
            `True` if the current user should come before `other`
            in sorted order, `False` otherwise.
    
        Examples
        --------
        >>> user1 = User('Robert', 'Johnson', 100001, 'bobby@example.com')
        >>> user2 = User('Alice', 'Smith', 200002, 'alice2008@fakemail.net')
        >>> user1 < user2
        True
        
        >>> user3 = User('Mario', 'Pérez', 333333, 'mario@example.com')
        >>> user4 = User('María', 'Pérez', 444444, 'maria@fakemail.net')
        >>> user3 < user4
        False
        
        >>> user5 = User('John', 'Doe', 900005, 'johny@example.com')
        >>> user6 = User('John', 'Doe', 900006, 'j.doe@fakemail.net')
        >>> user5 < user6
        True
        
        """
        tup_self = (
            normalize(self.last_name),
            normalize(self.first_name),
            self.id_number,
        )
        tup_other = (
            normalize(other.last_name),
            normalize(other.first_name),
            other.id_number,
        )
        return tup_self < tup_other


class Group():
    """
    Represents a group of users identified by a unique group ID.

    Parameters
    ----------
    group_id : str
        The unique identifier for the group, such as 'A', 'C3.2'
        or 'Group 2_1'. Commas are not permitted.
    members : collection of User, or None, optional
        A collection of User instances.
        Defaults to None if not provided.
        If `None`, the group is initialized with no members.

    Attributes
    ----------
    group_id : str
        The human-readable name of the group.
    members : tuple of User
        The users who are members of the group. Those users whose
        `.groups_ids` attribute does not contain the `self.group_id`
        won't be included in this tuple. Regardless of the input
        type, the value is stored internally as a tuple.

    Examples
    --------
    >>> group1 = Group('Group 1')
    >>> print(group1)
    Group('Group 1')
    >>> group1.group_id
    'Group 1'
    >>> group1.members
    ()
    
    >>> user1 = User('Chris', 'Doe', 111111, 'chris@example.com', 'A')
    >>> user2 = User('Sally', 'Smith', 222222, 'sally@nomail.net', ['A', 'G3'])

    >>> group2 = Group('A', [user1])
    >>> group2.members
    (User('Chris Doe', 111111),)
    
    >>> group3 = Group('A', [user1, user2])
    >>> group3.members
    (User('Chris Doe', 111111), User('Sally Smith', 222222))

    >>> group4 = Group('G3', [user1, user2])
    >>> group4.members
    (User('Sally Smith', 222222),)
    
    """
    def __init__(self, group_id, members=None):
        self.group_id = group_id
        if members is None:
            self.members = ()
        else:
            lst = [user for user in members if group_id in user.group_ids]
            self.members = tuple(sorted(lst, key=repr))

    def __repr__(self):
        return f'{self.__class__.__name__}({self.group_id!r})'

    def __lt__(self, other):
        tup_self = (
            normalize(self.group_id),
            self.members,
        )
        tup_other = (
            normalize(other.group_id),
            other.members,
        )
        return tup_self < tup_other


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

    Attributes
    ----------
    course_id : int
        The Moodle-assigned course identifier.
    users : tuple of User
        All users enrolled in the course, sorted by last name.
    groups : tuple of Group
        All groups in the course, sorted alphabetically.

    Class Methods
    -------------
    from_participants_csv(course_id)
        Constructs a Course instance from a Moodle CSV file named
        `courseid_<course_id>_participants.csv`. The file must have
        five columns: "First name", "Last name", "ID number",
        "Email address", and "Groups". Group names must be
        comma-separated.

    Examples
    --------
    >>> course_id = 12345
    >>> user1 = User('Sally', 'Smith', 111111, 'sally@gmail.com', ['A', 'X'])
    >>> user2 = User('Joe', 'Bloggs', 222222, 'joe@yahoo.com', ['A', 'Y'])
    >>> user3 = User('Jane', 'Roe', 333333, 'jenny@hotmail.com', ['B', 'X'])
    >>> user4 = User('John', 'Doe', 444444, 'johny@example.com', ['B', 'Y'])
    >>> user5 = User('Mary', 'Stewart', 555555, 'mary@nomail.com', ['C'])
    >>> user6 = User('Alfred', 'Miller', 666666, 'freddy@nomail.com')
    >>> users = [user1, user2, user3, user4, user5, user6]
    
    >>> course1 = Course(12345, users)
    >>> for user in course1.users: print(user)
    User('Joe Bloggs', 222222)
    User('John Doe', 444444)
    User('Alfred Miller', 666666)
    User('Jane Roe', 333333)
    User('Sally Smith', 111111)
    User('Mary Stewart', 555555)
    >>> for group in course1.groups: print(group)
    Group('A')
    Group('B')
    Group('C')
    Group('X')
    Group('Y')

    >>> csv_file = Path('.', f'courseid_{course_id}_participants.csv')
    >>> header = '"First name","Last name","ID number","Email address",Groups'
    >>> with open(csv_file, 'w') as f:
    ...     print(header, file=f)
    ...     print('Sally,Smith,111111,sally@gmail.com,"A, G1"', file=f)
    ...     print('Joe,Bloggs,222222,joe@yahoo.com,"A, G2"', file=f)
    ...     print('Jane,Roe,333333,jenny@hotmail.com,"B, G1"', file=f)
    ...     print('John,Doe,444444,johny@example.com,"B, G2"', file=f)
    ...     print('Robert,Johnson,555555,bob@fakemail.com,""', file=f)
    ...     print('Alfred,666666,freddy@nomail.com,"A, B"', file=f)
    ...     print('Mary,Stewart,777777', file=f)
    ...
    
    >>> course2 = Course.from_participants_csv(course_id, '.')
    Incomplete user info: ['Alfred', '666666', 'freddy@nomail.com', 'A, B']
    Incomplete user info: ['Mary', 'Stewart', '777777']
    >>> type(course2.users)
    <class 'tuple'>
    >>> for user in course2.users:
    ...     print(user)
    ...
    User('Joe Bloggs', 222222)
    User('John Doe', 444444)
    User('Robert Johnson', 555555)
    User('Jane Roe', 333333)
    User('Sally Smith', 111111)
    >>> type(course2.groups)
    <class 'tuple'>
    >>> for group in course2.groups: print(group)
    Group('A')
    Group('B')
    Group('G1')
    Group('G2')

    """
    n_columns = 5
    idx_first_name = 0
    idx_last_name = 1
    idx_id_number = 2
    idx_email = 3
    idx_group_ids = 4
    
    def __init__(self, course_id, users):
        self.course_id = course_id
        self.users = tuple(sorted(users))
        self.groups = self.get_groups()
        
    def __repr__(self):
        return f'{self.__class__.__name__}({self.course_id})'

    def get_groups(self):
        mapping = defaultdict(list)
        for user in self.users:
            for group_id in user.group_ids:
                mapping[group_id].append(user)
        groups = [Group(group_id, users)
                  for group_id, users in mapping.items()]
        return tuple(sorted(groups, key=lambda g: normalize(repr(g))))
        
    @classmethod
    def from_participants_csv(cls, course_id, data_folder):
        filename = f'courseid_{course_id}_participants.csv'
        csv_file = Path(data_folder, filename)
        users = []
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for line in reader:
                if len(line) < cls.n_columns:
                    print(f'Incomplete user info: {line}')
                    continue  # Skip malformed rows
                first_name = line[cls.idx_first_name].strip()
                last_name = line[cls.idx_last_name].strip()
                try:
                    id_number = int(line[cls.idx_id_number].strip())
                except ValueError:
                    id_number = None
                email = line[cls.idx_email].strip()
                valid_ids = set()
                for raw_id in line[cls.idx_group_ids].split(','):
                    valid_ids.add(raw_id.strip())
                valid_ids.discard('')
                group_ids = sorted(valid_ids, key=normalize)
                user = User(first_name, last_name, id_number, email, group_ids)
                users.append(user)
        return cls(course_id, users)


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
    html_path : pathlib.Path
        Path to the HTML report file exported from Moodle.

    Attributes
    ----------
    html_path : pathlib.Path
        Path to the HTML report file exported from Moodle.
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
        Computed grades for each user. Each key is a user's ID; 
        each value is a dictionary with keys 'submission' and
        'overall', representing the group submission score 
        and the total grade (submission + assessment).
    """
    def __init__(self, html_path):
        self.html_path = html_path
        self.soup = self.get_soup()
        self.workshop_title = mwrp.extract_workshop_title(self.soup)
        self.course = self.get_course()
        self.group_ids = mwrp.extract_group_ids(self.soup)
        self.grades_from_report = mwrp.extract_grades(self.soup)
        # Since not all enrolled users necessarily participate in the
        # workshop, the number of graded users may differ from the
        # total number of users:
        # len(self.grades) != len(self.course.users)
        self.grades = self.compute_grades()


    def get_soup(self):
        """
        Read the specified HTML file and parse its content using 
        BeautifulSoup with the 'lxml' parser.
    
        Returns
        -------
        bs4.BeautifulSoup
            Parsed HTML content of the grades report, used
            internally for extracting information.
        """
        with open(self.html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return BeautifulSoup(html_content, 'lxml')
        
    
    def get_course(self):
        """
        Load course participant data based on the course ID.

        This method extracts the course ID from the workshop's HTML
        report and uses it to instantiate a `Course` object by reading
        the corresponding CSV file. The CSV file is expected to be
        named `courseid_<id>_participants.csv` and to be stored in the
        same folder as the HTML file.

        Returns
        -------
        course_obj : Course
            A `Course` object containing the list of users and groups
            associated with the workshop's course.

        See Also
        --------
        Course.from_participants_csv : Method that reads and parses
        the CSV participant list.
        
        """
        course_id = mwrp.extract_course_id(self.soup)
        data_folder = self.html_path.parent
        course_obj = Course.from_participants_csv(course_id, data_folder)
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


    def compute_grades(self): # !!! Docstring
        grades = dict()
        workshop_groups = self.get_workshop_groups()
        for group in workshop_groups:
            full_names = [member.full_name for member in group.members]
            received = []
            for full_name in full_names:
                # As a student cannot belong to more than one group,
                # we can initialize the value associated with its
                # full name (the key) with an empty dictionary
                grades[full_name] = dict()
                mapping = self.grades_from_report[full_name]
                # Storing the received grades in a list rather than
                # in a dictionary makes it possible that the number
                # of graders could be less than the number of grades
                # (for instance, if a student is assigned the
                # submissions of two members of the same group).
                received.extend(mapping['received'].values())
            if received:
                group_grade = sum(received)/len(received)
            else:
                group_grade = mwrp.NULL_GRADE
            for full_name in full_names:
                if self.grades_from_report[full_name]['submitted']:
                    grades[full_name]['submission'] = group_grade
                else:
                    grades[full_name]['submission'] = 0
        for full_name in grades:
            # `submission` cannot be `mwrp.NULL_GRADE`
            submission = grades[full_name]['submission']
            assessment = self.grades_from_report[full_name]['grading']
            assessment = assessment if assessment is not mwrp.NULL_GRADE else 0
            # We assume that submission and assessment grades are
            # properly normalized and therefore can be summed up
            grades[full_name]['overall'] = submission + assessment
        return grades
    
    
    def display_grades(self):
        print('ID number  Name                        '
              '  Submission  Assessment  Overall\n'
              '------------------------------------'
              '------------------------------------')
        for user in sorted(self.course.users):
            full_name = user.full_name
            if full_name in self.grades:
                submission = self.grades[full_name]['submission']
                assessment = self.grades_from_report[full_name]['grading']
                if assessment == mwrp.NULL_GRADE:
                    assessment = 0
                overall = self.grades[full_name]['overall']
                print(f'{user.id_number:<9d}  '
                      f'{user.full_name:30}{submission:10.2f}'
                      f'{assessment:12.2f}{overall:9.2f}')


    def save_grades(self, filename):
        """
        Export computed workshop grades to a CSV file.

        This method writes a table of final grades to the specified 
        CSV file. For each user enrolled in the course, it includes 
        their ID number, full name, submission grade (shared within 
        their group), individual assessment grade, and overall grade 
        (the weighted sum of submission and assessment).

        Grades are written in a sorted order based on user last
        names. Users without recorded submission or assessment
        grades are excluded from the output.

        Parameters
        ----------
        filename : str
            Path to the CSV file where the grades will be saved.
        
        Output Format
        -------------
        The CSV file includes the following columns:
        - ID number
        - Name (First Last)
        - Submission (float, two decimal places)
        - Assessment (float, two decimal places)
        - Overall (float, two decimal places)
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([
                'ID number',
                'Name',
                'Submission',
                'Assessment',
                'Overall',
            ])
            for user in sorted(self.course.users):
                full_name = user.full_name
                if full_name in self.grades.keys():
                    submission = self.grades[full_name]['submission']
                    assessment = self.grades_from_report[full_name]['grading']
                    if assessment == mwrp.NULL_GRADE:
                        assessment = 0
                    overall = self.grades[full_name]['overall']
                    writer.writerow([
                        user.id_number,
                        user.full_name,
                        f'{submission:4.2f}',
                        f'{assessment:4.2f}',
                        f'{overall:4.2f}',
                    ])


if __name__ == '__main__':
    doctest.testmod()