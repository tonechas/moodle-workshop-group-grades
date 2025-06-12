"""
Helper functions for parsing a Moodle workshop grades report
exported as a `bs4.BeautifulSoup` object.
"""

import doctest
import re


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


def get_grade(grade_tag):
    """
    Extract a numeric grade from a tag.

    Handles both dot and comma as decimal separators.

    Parameters
    ----------
    grade_tag : bs4.element.Tag
        A BeautifulSoup tag containing a grade as text.

    Returns
    -------
    float
        The extracted numeric grade.
            
    Examples
    --------
    >>> from bs4 import BeautifulSoup
    >>> tag1 = BeautifulSoup(
    ...     '<span class="grade">70,4</span>', 'lxml'
    ... ).span
    >>> get_grade(tag1)
    70.4
    >>> tag2 = BeautifulSoup(
    ...     '<span class="grade">81.3</span>', 'lxml'
    ... ).span
    >>> get_grade(tag2)
    81.3
    """
    text = grade_tag.get_text(strip=True)
    try:
        grade = float(text)
    except ValueError:
        # Decimal separator can be a ','
        grade = float(text.replace(',', '.'))
    return grade


def extract_workshop_title(soup):
    """
    Extract the title of the current workshop from the breadcrumb.

    The workshop title is assumed to be the last `<li>` element
    within the breadcrumb navigation bar of the HTML document.

    Parameters
    ----------
    soup : bs4.BeatifulSoup
        The content of a workshop grades report (Moodle page).

    Returns
    -------
    str
        The title of the workshop, with surrounding whitespace
        removed.
    
    Examples
    --------
    >>> from bs4 import BeautifulSoup
    >>> ol = '''
    ...     <ol class="breadcrumb">
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../index.php?categoryid=919"  >
    ...                 2024/2025
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../index.php?categoryid=921"  >
    ...                 Oficial programs
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../index.php?categoryid=949"  >
    ...                 Bachelor's degree in Marine Science
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../view.php?id=22862&amp;section=7"
    ...               title="Geology for Dummies">
    ...                 Course code
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <span>Workshop: Carbonate Content Analysis</span>
    ...         </li>
    ...     </ol>'''
    >>> soup = BeautifulSoup(ol, 'lxml')
    >>> extract_workshop_title(soup)
    'Workshop: Carbonate Content Analysis'
    """
    breadcrumb = soup.find('ol', class_='breadcrumb')
    last_li = breadcrumb.find_all('li')[-1]
    return last_li.get_text(strip=True)


def extract_course_title(soup):
    """
    Extract the course title from the breadcrumb navigation bar.

    The course title is obtained from the first `<a>` tag in the
    breadcrumb that includes a `title` attribute.

    Parameters
    ----------
    soup : bs4.BeatifulSoup
        The content of a workshop grades report (Moodle page).

    Returns
    -------
    str
        The title of the course, as specified in the `title`
        attribute of the corresponding link.
    
    Examples
    --------
    >>> from bs4 import BeautifulSoup
    >>> ol = '''
    ...     <ol class="breadcrumb">
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../index.php?categoryid=919"  >
    ...                 2024/2025
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../index.php?categoryid=921"  >
    ...                 Oficial programs
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../index.php?categoryid=949"  >
    ...                 Bachelor's degree in Marine Science
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <a href="https://.../view.php?id=22862&amp;section=7"
    ...               title="Geology for Dummies">
    ...                 Course code
    ...             </a>
    ...         </li>
    ...         <li class="breadcrumb-item">
    ...             <span>Workshop: Carbonate Content Analysis</span>
    ...         </li>
    ...     </ol>'''
    >>> soup = BeautifulSoup(ol, 'lxml')
    >>> extract_course_title(soup)
    'Geology for Dummies'
    """
    breadcrumb = soup.find('ol', class_='breadcrumb')
    for a_tag in breadcrumb.find_all('a'):
        if a_tag.has_attr('title'):
            return a_tag['title']


def extract_course_id(soup):
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

    Raises
    ------
    AttributeError
        If the breadcrumb or the expected link structure
        is not found.
    """
    for script_tag in soup.find_all('script'):
        content = script_tag.string
        if not content or 'courseId' not in content:
            continue
        found = re.search(r'"courseId"\s*:\s*(\d+)', content)
        if found:
            return int(found.group(1))
    raise AttributeError('Unable to extract "courseId".')


def extract_group_ids(soup):
    """
    Extract the list of group names from the group selection menu.

    Finds the `<select>` element used to choose participant groups,
    and collects the text content of all `<option>` elements except
    the default "All participants" entry.

    Parameters
    ----------
    soup : bs4.BeatifulSoup
        The content of a workshop grades report (Moodle page).

    Returns
    -------
    list of str
        A sorted list of group names as they appear in the
        dropdown menu.

    Examples
    --------
    >>> from bs4 import BeautifulSoup
    >>> form = '''
    ...     <form method="get" action="https://.../view.php"
    ...             class="form-inline" id="selectgroup">
    ...         <input type="hidden" name="id" value="1137354">
    ...         <label for="single_select68359598e10ee12">
    ...             Visible groups (groups.w)
    ...         </label>
    ...         <select  id="single_select68359598e10ee12"
    ...             class="custom-select singleselect" name="group">
    ...             <option  value="0" selected>All participants</option>
    ...             <option  value="88465" >Group 1_1</option>
    ...             <option  value="88466" >Group 1_2</option>
    ...             <option  value="88470" >Group 2_1</option>
    ...             <option  value="88471" >Group 2_2</option>
    ...             <option  value="88472" >Group 2_3</option>
    ...         </select>
    ...         <noscript>
    ...             <input type="submit" class="btn btn-secondary ml-1"
    ...                 value="Go to">
    ...         </noscript>
    ...     </form>'''
    >>> soup = BeautifulSoup(form, 'lxml')
    >>> extract_group_ids(soup)
    ['Group 1_1', 'Group 1_2', 'Group 2_1', 'Group 2_2', 'Group 2_3']
    """
    select_tag = soup.find('select', attrs={
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


def extract_rows(soup):
    """
    Extract relevant table rows from the grades report.

    Parses the first `<table>` element in the HTML document and
    collects all `<tr>` elements within its `<tbody>` that are not
    marked with specific structural classes, except for 'lastrow'.

    Parameters
    ----------
    soup : bs4.BeatifulSoup
        The content of a workshop grades report (Moodle page).

    Returns
    -------
    list of bs4.element.Tag
        A list of `<tr>` tags corresponding to participant
        data rows.

    Raises
    ------
    AttributeError
        If no `<table>` or `<tbody>` is found in the parsed HTML.
    """
    tables = soup.find_all('table')
    if not tables:
        raise AttributeError('No <table> elements found in `soup`.')
    first_table = tables[0]
    tbody = first_table.find('tbody')
    if tbody is None:
        raise AttributeError('No <tbody> found in the first table.')
    rows = []
    for tr in tbody.find_all('tr'):
        if tr.has_attr('class') and tr['class'] in ([], ['lastrow']):
            rows.append(tr)
    return rows

# @staticmethod
# def extract_participants(soup): #!!! Not used
#     """
#     Extract the participant names from the grades report.

#     Iterates over the table rows and retrieves the participant's
#     full name from the appropriate `<td>` element, based on known
#     CSS classes.

#     Returns
#     -------
#     list of str
#         A list of participant names as they appear in the report.
#     """
#     participants = []
#     for row in self.extract_rows():
#         td = row.find('td',class_=lambda x: x in PARTICIPANT_CELLS)
#         if td:
#             participants.append(td.contents[-1].text)
#     return participants


def extract_grades(soup):
    """
    Extract peer assessment grades from the workshop report table.

    Parses each relevant table row to build a nested dictionary of
    grades, including:
    - Grades received by each participant from peers.
    - Grades given by each participant to peers.
    - The assessment grade assigned to each participant.

    Also performs a consistency check to ensure that received and
    given grades match symmetrically across participants.

    Parameters
    ----------
    soup : bs4.BeatifulSoup
        The content of a workshop grades report (Moodle page).

    Returns
    -------
    dict
        A dictionary where keys are participant names (str), and
        values are dictionaries with the following structure:
        {
            'received': {grader_name: grade, ...},
            'given': {gradee_name: grade, ...},
            'assessment': float or str (if NULL_GRADE)
        }

    Raises
    ------
    ValueError
        If a mismatch is found between received and given grades.
    """
    grades = dict()
    for row in extract_rows(soup):
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
            grade = get_grade(grade_tag)
            grades[participant]['received'][grader] = grade
        td_given = row.find('td', class_=lambda x: x in GIVEN_GRADE_CELLS)
        if td_given:
            fullname_tag = td_given.find('span', class_='fullname')
            gradee = fullname_tag.get_text(strip=True)
            grade_tag = td_given.find('span', class_='grade')
            grade = get_grade(grade_tag)
            grades[participant]['given'][gradee] = grade
        td_grad = row.find('td', class_=lambda x: x in GRADING_GRADE_CELLS)
        if td_grad:
            if td_grad.get_text() != NULL_GRADE:
                grade = get_grade(td_grad)
                grades[participant]['assessment'] = grade
    # Sanity check
    for gradee in grades:
        for grader in grades[gradee]['received']:
            gradee_from_grader = grades[gradee]['received'][grader]
            grader_to_gradee = grades[grader]['given'][gradee]
            if gradee_from_grader != grader_to_gradee:
                raise ValueError('Error parsing grades')
    return grades


if __name__ == '__main__':
    doctest.testmod()