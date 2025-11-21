"""
Helper functions for parsing a Moodle workshop grades report
exported as a `bs4.BeautifulSoup` object.
"""

import doctest
import re


NULL_GRADE = '-'

NO_SUBMISSION = (
    'No submission found for this user',
    'No se han encontrado envíos de este usuario',
    'Non se atoparon entregas deste usuario',
)

PARTICIPANT_CELLS = (
    'participant cell c0',
)

SUBMISSION_CELLS = (
    'submission cell c1',
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

SUBMISSION_GRADE_CELLS = (
    'submissiongrade cell c3',
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
        If the script or the courseId is not found.

    Examples
    --------
    >>> from bs4 import BeautifulSoup
    >>> good_script = '''
    ...     <script>
    ...     var M = {}; M.yui = {};
    ...     M.pageloadstarttime = new Date();
    ...     M.cfg = {"admin":"admin","language":"en","courseId":22862};
    ...     YUI_config = {"debug":false};
    ...     M.yui.loader = {modules: {}};
    ...     </script>'''
    >>> good_soup = BeautifulSoup(good_script, 'lxml')
    >>> extract_course_id(good_soup)
    22862
    >>> bad_script = '''
    ...     <script>
    ...     var M = {}; M.yui = {};
    ...     M.pageloadstarttime = new Date();
    ...     M.cfg = {"admin":"admin","language":"en"};
    ...     YUI_config = {"debug":false};
    ...     M.yui.loader = {modules: {}};
    ...     </script>'''
    >>> bad_soup = BeautifulSoup(bad_script, 'lxml')
    >>> extract_course_id(bad_soup) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    AttributeError: Unable to extract "courseId".
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
    - A boolean flag indicating whether the student submitted
      an assignment.
    - Grades received by each participant from peers.
    - Grades given by each participant to peers.
    - The submission grade assigned to each participant by Moodle.
    - The grading grade assigned to each participant by Moodle.

    Also performs a consistency check to ensure that received and
    given grades match symmetrically across participants.

    Parameters
    ----------
    soup : bs4.BeatifulSoup
        The content of a workshop grades report (Moodle page).

    Returns
    -------
    dict
        A dictionary where keys are participant full names (str),
        and values are dictionaries with the following structure:
        {
            'submitted': bool,
            'received': {grader_id: grade, ...},
            'given': {gradee_id: grade, ...},
            'submission': float or str (if NULL_GRADE),
            'grading': float or str (if NULL_GRADE)
        }

    Raises
    ------
    ValueError
        If a mismatch is found between received and given grades
        or duplicated full names are detected.
    """
    view_id_to_grades = dict()
    alt_to_grades = dict()
    view_id_to_alt = dict()
    for row in extract_rows(soup):
        # Extract participant view_id (from link) and full name (`alt`)
        td_participant = row.find(
            'td',
            class_=lambda x: x in PARTICIPANT_CELLS,
        )
        if td_participant:
            try:
                link = td_participant.find('a', class_='d-inline-block aabtn')
                match_id = re.search(r'id=(\d+)', link['href'])
                participant_view_id = int(match_id.group(1))
                #img = td_participant.find('img')
                #if img and img.get("alt"):
                #    participant_alt = img["alt"].strip()
                #else:
                spans = td_participant.find_all("span")
                #if spans:
                participant_alt = spans[-1].get_text(strip=True)
                view_id_to_alt[participant_view_id] = participant_alt
            except BaseException as ex:
                print(ex)
                print('Skipping malformed participant cell')
            view_id_to_grades[participant_view_id] = {
                'submitted': False,
                'received': dict(),
                'given': dict(),
                'submission': NULL_GRADE,
                'grading': NULL_GRADE,
            }

        # Set 'submitted' to True is a submission is found 
        td_submission = row.find('td', class_=lambda x: x in SUBMISSION_CELLS)
        if td_submission:
            title_tag = td_submission.find('a', class_='title')
            if title_tag:
                view_id_to_grades[participant_view_id]['submitted'] = True

        # Extract received grades
        td_received = row.find(
            'td',
            class_=lambda x: x in RECEIVED_GRADE_CELLS,
        )
        if td_received:
            try:
                link = td_received.find('a', class_='d-inline-block aabtn')
                match_id = re.search(r'id=(\d+)', link['href'])
                grader_view_id = int(match_id.group(1)) if match_id else None
                grade_tag = td_received.find('span', class_='grade')
                grade = get_grade(grade_tag)
                view_id_to_grades[participant_view_id]['received'][grader_view_id] = grade
            except BaseException as ex:
                print(ex)
                print('Skipping malformed receivedgrade cell')
                
        # Extract given grades
        td_given = row.find('td', class_=lambda x: x in GIVEN_GRADE_CELLS)
        if td_given:
            try:
                link = td_given.find('a', class_='d-inline-block aabtn')
                match_id = re.search(r'id=(\d+)', link['href'])
                gradee_view_id = int(match_id.group(1))
                grade_tag = td_given.find('span', class_='grade')
                grade = get_grade(grade_tag)
                view_id_to_grades[participant_view_id]['given'][gradee_view_id] = grade
            except BaseException as ex:
                print(ex)
                print('Skipping malformed receivedgrade cell')

        # Extract submission grade
        td_submission_grade = row.find(
            'td',
            class_=lambda x: x in SUBMISSION_GRADE_CELLS,
        )
        if td_submission_grade:
            if td_submission_grade.get_text() != NULL_GRADE:
                grade = get_grade(td_submission_grade)
                view_id_to_grades[participant_view_id]['submission'] = grade

        # Extract submission grade
        td_grading_grade = row.find(
            'td',
            class_=lambda x: x in GRADING_GRADE_CELLS,
        )
        if td_grading_grade:
            if td_grading_grade.get_text() != NULL_GRADE:
                grade = get_grade(td_grading_grade)
                view_id_to_grades[participant_view_id]['grading'] = grade

    # Sanity checks
    for gradee in view_id_to_grades:
        for grader in view_id_to_grades[gradee]['received']:
            gradee_from_grader = view_id_to_grades[gradee]['received'][grader]
            grader_to_gradee = view_id_to_grades[grader]['given'][gradee]
            if gradee_from_grader != grader_to_gradee:
                raise ValueError('Error parsing grades')
    if len(view_id_to_alt) > len(set(view_id_to_alt.keys())):
        raise ValueError('Different users have identical full names')
        

    # Change key of dictionary
    for participant_view_id in view_id_to_grades:
        alt = view_id_to_alt[participant_view_id]
        received = dict()
        for grader_view_id, grade in view_id_to_grades[participant_view_id]['received'].items():
            received[view_id_to_alt[grader_view_id]] = grade
        given = dict()
        for gradee_view_id, grade in view_id_to_grades[participant_view_id]['given'].items():
            given[view_id_to_alt[gradee_view_id]] = grade
        alt_to_grades[alt] = {
            'submitted': view_id_to_grades[participant_view_id]['submitted'],
            'received': received,
            'given': given,
            'submission': view_id_to_grades[participant_view_id]['submission'],
            'grading': view_id_to_grades[participant_view_id]['grading'],
        }
    return alt_to_grades


if __name__ == '__main__':
    doctest.testmod()