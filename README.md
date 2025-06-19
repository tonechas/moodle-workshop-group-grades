# moodle-workshop-group-grades
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![Moodle 4.01](https://img.shields.io/badge/moodle-4.01-orange.svg)](https://moodle.org/)

Tool for parsing Moodle Workshop grades report to extract peer assessments and compute group submission grades.


## Installation

1. Clone this repository:
```console
$ git clone https://github.com/tonechas/moodle-workshop-group-grades.git
```

2. Create a virtual environment:
```console
$ python -m venv path\to\venvs\directory\mwgg python=3.13.2
```

3. Activate the virtual environment:
```console
$ path\to\venvs\directory\mwgg\Scripts\activate
```

4. Install the dependencies:
```console
(mwgg) $ pip install -r path\to\venvs\directory\mwgg\requirements.txt
```

## Usage
To run the script, execute the following command:
```console
(mwgg) $ python path\to\venvs\directory\mwgg\mwgg.py
```

After that, a dialog box will appear prompting you to select the directory containing the two required data files.

### `courseid_<course_id>_participants.csv`

This file can be generated as follows:
- Go to "Participants" in your Moodle course.
- Select all users.
- In the "With selected users..." dropdown menu select the "Download table as comma separated values (.csv)" option.

Notice that you have to replace `<course_id>` by the ID of your course, for example `12345`. The course data file is organized as shown below:
```text
"First name",Surname,"Email address",Groups
Peter,Smith,pete@gmail.com,"A, G1_1"
Jane,Bloggs,jenny@yahoo.com,"B, G1_1"
Alice,Johnson,alicej@hotmail.com,"B, G1_2"
John,Doe,johny@example.com,G2_2
Michael,Harris,mike2007@fakemail.net,G3_1
Emily,Carter,milly@.test.com,"A, G3_2"
```

### `<workshop_id>.htm`

This is the HTML code of the Workshop grades report. Note that `<workshop_id>` must be replaced by an identifier, for example `HISTORY204D-essay` or `CS101-project`. The report looks like this.

<figure>
  <img src="https://grok.lsu.edu/image/56192.jpg" alt="Screenshot of Workshop grades report" width="auto">
  <figcaption>Source: <a href="https://grok.lsu.edu/article.aspx?articleid=56192">GROK Knowledge Base, LSU</a></figcaption>
</figure>

### `<workshop_id>.csv`

This file is the output produced by the script execution. The file is structured into four columns:
```text
Email address,Submission,Assessment,Overall
pete@gmail.com,72.45,91.00,76.16
jenny@yahoo.com,72.45,86.50,75.26
alicej@hotmail.com,69.37,72.35,60.97
johny@example.com,69.37,78.20,71.14
mike2007@fakemail.net,81.26,92.30,83.47
milly@.test.com,81.26,94.15,83.84
```
Then you have to complete the following steps:
1. In your Moodle course, go to **Grades** → **Import** and choose **CSV file**.
2. Upload your `.csv` file.
3. In **Identify user by**, select the field that matches your file (e.g., **Email address**).
4. Match each column in your file to an existing grade item or choose to **create a new grade item**.
5. Click **Upload grades**. Moodle will confirm how many grades were updated.
