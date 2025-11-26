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
(mwgg) $ pip install -r path\to\moodle-workshop-group-grades\requirements.txt
```

## Usage
To run the script, execute the following command:
```console
(mwgg) $ python path\to\moodle-workshop-group-grades\mwgg.py
```

After that, a dialog box will appear prompting you to select the directory containing the two required data files.

### `courseid_<course_id>_participants.csv`

This file can be generated as follows:
- Go to **Participants** in your Moodle course.
- Select all users.
- In the **With selected users...** dropdown menu select the **Download table as comma separated values (.csv)** option.

Notice that you have to replace `<course_id>` by the ID of your course, for example `12345`. The course data file must be organized as shown below:
```text
"First name","Last name","ID number","Email address",Groups
Peter,Smith,300000,pete@gmail.com,"A, G1_1"
Jane,Bloggs,300001,jenny@yahoo.com,"B, G1_1"
Alice,Johnson,112233,alicej@hotmail.com,"B, G1_2"
John,Doe,444555,johny@example.com,G2_2
Michael,Harris,100100,mike2007@fakemail.net,G3_1
Emily,Carter,670670,milly@test.com,"A, G3_2"
```

### `<workshop_id>.html`

This is the HTML code of the Workshop grades report. Note that `<workshop_id>` should be replaced by an identifier, for example `HISTORY204D-essay` or `CS101-project`. The report looks like this:

<figure>
  <img src="https://grok.lsu.edu/image/56192.jpg" alt="Screenshot of Workshop grades report" width="auto">
  <figcaption>Source: <a href="https://grok.lsu.edu/article.aspx?articleid=56192">GROK Knowledge Base, LSU</a></figcaption>
</figure>

### `<workshop_id>.csv`

This file is the output produced by the script execution. The file is structured into four columns:
```text
ID number,Name,Submission,Assessment,Overall
300000,Peter Smith,62.45,19.15,81.60
300001,Jane Bloggs,73.45,16.50,89.95
112233,Alice Johnson,49.37,17.35,66.72
444555,John Doe,38.57,15.21,53.78
100100,Michael Harris,34.26,12.30,46.56
670670,Emily Carter,61.50,18.25,79.75
```
In the sample output data file above Submission ranges from 0 to 80, and Assessment ranges from 0 to 20. Overall is simply the sum of Submission and Assessment.

Then you have to complete the following steps:
1. In your Moodle course, go to **Grades** → **Import** and choose **CSV file**.
2. Upload your `<workshop_id>.csv` file.
3. In **Identify user by**, select the field that matches your file (e.g., **ID number**).
4. Match each column in your file to an existing grade item or choose to **create a new grade item**.
5. Click **Upload grades**. Moodle will confirm how many grades were updated.

## Project Background

This repository has been developed to support the research presented in the article _"Extending Moodle's Workshop Functionality to Support Group Submissions and Evaluations”_, which is currently under review for publication in the *Journal of College Science Teaching*.