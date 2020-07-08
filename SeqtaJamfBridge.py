###########################################################################################################
###########################################################################################################
##                                         SeqtaJamfBridge                                               ##
##                                          Jacob Curulli                                                ##
## This code is shared as is, under Creative Commons Attribution Non-Commercial 4.0 License              ##
## Permissions beyond the scope of this license may be available at http://creativecommons.org/ns        ##
###########################################################################################################

import psycopg2
import xml.etree.ElementTree as ET
import csv
import configparser
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import numpy as np

# Get the date
dateNow = datetime.now()

# Read the config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# read config file for seqta database connection details
db_user=config['db']['user']
db_port=config['db']['port']
db_password=config['db']['password']
db_database=config['db']['database']
db_host=config['db']['host']
db_sslmode=config['db']['sslmode']

# read config file for other details
jamf_classesAdminUsername=config['classes']['classesAdminUsername']
jamf_address=config['classes']['jamfAddress']
jamf_apiUsername=config['classes']['jamfApiUsername']
jamf_apiPassword=config['classes']['jamfApiPassword']

# declare some variables here so we can make sure they are present
currentYear = dateNow.strftime("%Y")
print("current year is:", currentYear)

# file locations, this can be changed to suit your environment
csvApprovedClasses = "approved_classes.csv"
csvKnownClasses = "known_classes.csv"

# Format URL
jamfUrl = jamf_address + "/JSSResource/classes/id/"

payload = {}
headers = {
  'Accept': 'application/xml, application/json',
  'Content-Type': 'application/xml',
  'Authorization': 'Basic amN1cnVsbGk6QnJlaXRlbmZlbGQ3OFRha2VuaSw=',
  'Cookie': 'APBALANCEID=aws.apse2-std-pewaukee2-tc-7'}

# Import CSV file for approved class lists
try:
    with open(csvApprovedClasses, newline='', encoding='utf-8-sig') as csvfile:
        classList = list(csv.reader(csvfile))
        print (type(classList))
        print (classList)
        print ("Number of approved classes imported from csv list: ",len(classList))
except:
    print("***************************")
    print("Error importing csv file")

# Import CSV file for known class lists with Jamf Class Id's
try:
    with open(csvKnownClasses, newline='', encoding='utf-8-sig') as csvKnownClassesfile:
        knownClassList = list(csv.reader(csvKnownClassesfile))
        print (type(knownClassList))
        print (knownClassList)
        print ("Number of known classes imported from csv list: ",len(knownClassList))
        npKnownClassList = np.array(knownClassList)
except:
    print("***************************")
    print("Error importing csv known classes file")

# Method to upload data to Jamf
def upload_to_jamf(classNameSanitised, className, jamfData, npKnownClassList):
    print("inside the upload_to_jamf function")
    print("sanitized name is: " + classNameSanitised)
    print("unsanitized name is: " + className)
    print(npKnownClassList)

    # First we check if there is already a known Jamf class ID for this class
    # We do this by checking the numpy array for a match to the className then we check the index and then access it
    # again to pull the class ID which is at index [1] for that matching row
    if np.in1d(className, npKnownClassList):
        print ("found class: " + className)
        classIndex = (np.where(npKnownClassList == className)[0][0])
        jamfClassId = npKnownClassList[classIndex][1]
        print ("jamf class id below please.....")
        print (jamfClassId)

        # Now we will update the class
        url = (jamfUrl + jamfClassId)
        payload = jamfData
        headers = {'Content-Type': 'text/plain'}
        response = requests.request("PUT", url, auth=HTTPBasicAuth(jamf_apiUsername, jamf_apiPassword), headers=headers, data=payload)
        print(response.text.encode('utf8'))

    else:
        print ("Cant' find a class in the known list. We'll assume it is new and create a new class")

        # Now we will update the class
        url = (jamfUrl + "-1")
        payload = jamfData
        headers = {'Content-Type': 'text/plain'}
        response = requests.request("POST", url, auth=HTTPBasicAuth(jamf_apiUsername, jamf_apiPassword), headers=headers, data=payload)
        print(response.text.encode('utf8'))
        newId = response.text[49:-13]
        print (newId)
        with open('known_classes.csv', 'a', newline='\n') as fd:
            writer = csv.writer(fd)
            writer.writerow([(className), (newId)])

# Open connection to Seqta
try:
    connection = psycopg2.connect(user=db_user,
                                  port=db_port,
                                  password=db_password,
                                  database=db_database,
                                  host = db_host,
                                  sslmode = db_sslmode)
    cursor = connection.cursor()
    print(connection.get_dsn_parameters(), "\n")

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)

# Fetch data for classlists
for i in classList:
    pullDate = datetime.now().strftime("%Y.%m.%d")
    pullTime = datetime.now().strftime("%H:%M:%S")
    print("Pull date is", pullDate)
    print("Pull time is", pullTime)
    staffList = set()
    staffUsernameList = set()
    studentList = set()
    studentUsernameList = set()
    classArray = tuple()
    className = str(('[%s]' % ', '.join(map(str, (i))))[1:-1])
    classXMLFileName = str(className + ".xml")
    classNameSanitised = className.replace("#","%23")
    print ("**")
    print ("Class name is: " + className)
    print ("Sanitised class name is: " + classNameSanitised)
    print ("Class XML file name is: " + classXMLFileName)
    # Print PostgreSQL version
    cursor.execute("SELECT version();")
    record = cursor.fetchone()

    # Lookup classID from Class name in Seqta
    sq_classUnitQuery = "SELECT * FROM public.classunit WHERE name = (%s);"
    cursor.execute(sq_classUnitQuery,(className,))
    classUnitPull = cursor.fetchall()
    print("Getting class information for:", (className))
    for row in classUnitPull:
        classUnitID = row[0]
        classSubjectID = row[4]
        classTermID = row[7]

    print("Class unit ID (classUnitID) is:", classUnitID)
    print("Class subject ID (classSubjectID) is:", classSubjectID)
    print("Class term ID (classTermID) is:", classTermID)

    # Check if class has a staff member or students
    # If they don't we need to stop processing the class and drop it gracefully

    # Get subject description for Class
    sq_classSubjectQuery = "SELECT * FROM subject WHERE id = (%s);"
    cursor.execute(sq_classSubjectQuery, (classSubjectID,))
    classSubjectPull = cursor.fetchall()
    for row in classSubjectPull:
        classSubjectDescription = row[3]
        classSubjectName = row[2]
    classTeamName = (className + " - " + classSubjectDescription)
    print("Class subject Description (classSubjectDescription) is:", classSubjectDescription)
    print("Class team name (classTeamName) is:", classTeamName)
    print("Class subject Name (classSubjectName) is:", classSubjectName)

    # Get StaffID in this classUnit
    sq_staffIDQuery = "SELECT staff from public.classinstance WHERE classunit = (%s) and date <= current_date ORDER BY id DESC LIMIT 1;"
    cursor.execute(sq_staffIDQuery, (classUnitID,))
    staffID_pre = cursor.fetchone()
    if staffID_pre is None:
        print("Couldn't find a class today or previously for classunit:", classUnitID)
        print("Checking for a class up to 14 days in the future and selecting the closest date to today")
        sq_staffIDQuery = "SELECT staff from public.classinstance WHERE classunit = (%s) date = current_date + interval '14 day' ORDER BY id DESC LIMIT 1;"
        cursor.execute(sq_staffIDQuery, (classUnitID,))
        staffID_pre = cursor.fetchone()
        staffID = int(staffID_pre[0])
        print("Staff ID is:", (staffID))
        # Write to teacher ID list
        staffList.add(staffID)
    else:
        staffID = int(staffID_pre[0])
        print("Staff ID is:", (staffID))
        # Write to teacher ID list
        staffList.add(staffID)

    # Get Student ID's for this classUnit
    sq_studentIDListQuery = "SELECT student from \"classunitStudent\" WHERE classunit = (%s) and removed is NULL;"
    cursor.execute(sq_studentIDListQuery, (classUnitID,))
    studentIDArray = tuple([r[0] for r in cursor.fetchall()])
    print("List of students in class name:", className)
    print(studentIDArray)
    for row in studentIDArray:
        studentList.add(row)

    for staff in staffList:
        # Now get the staff information
        sq_staffQuery = "SELECT * from public.staff WHERE id = (%s);"
        cursor.execute(sq_staffQuery, (staff,))
        staffPull = cursor.fetchall()
        for row in staffPull:
            staffFirstName = row[4]
            staffLastName = row[7]
            staffUsername = row[21]
            staffUsernameList.add(staffUsername)

        print("Staff First Name (staffFirstName) is:", staffFirstName)
        print("Staff Last Name (staffLastName) is:", staffLastName)
        print("Staff username (staffUsername) is:", staffUsername)
        print("Staff ID is (staff) is:", staff)

    # Add any manually specified staff usernames
    staffUsernameList.add(jamf_classesAdminUsername)

    for student in studentList:
        # Now get the student information
        sq_studentQuery = "SELECT * from student WHERE id = (%s) AND status = 'FULL';"
        cursor.execute(sq_studentQuery, (student,))
        studentPull = cursor.fetchall()
        for row in studentPull:
            studentFirstName = row[3]
            studentLastName = row[6]
            studentUsername = row[47]
            studentUsernameList.add(studentUsername)

        print("Student First Name (studentFirstName) is:", studentFirstName)
        print("Student Last Name (studentLastName) is:", studentLastName)
        print("Student username (studentUsername) is:", studentUsername)
        print("Student ID is (student) is:", student)

    ###################################
    # Create XML data for Jamf
    ###################################
    jamfXMLData = ET.Element('class')
    jamfxmlClassName = ET.SubElement(jamfXMLData, 'name')
    jamfxmlClassDescription = ET.SubElement(jamfXMLData, 'description')
    jamfxmlClassStudents = ET.SubElement(jamfXMLData, 'students')
    jamfxmlClassTeachers = ET.SubElement(jamfXMLData, 'teachers')
    #jamfxmlClassTeacher = ET.SubElement(jamfxmlClassTeachers, 'teacher')

    jamfxmlClassName.text = (className)
    jamfxmlClassDescription.text = ("Last modified on: " + pullDate + " " + pullTime)
    #jamfxmlClassTeacher.text = (staffUsername)

    for s in staffUsernameList:
        # jamfxmlClassStudent = ET.SubElement(jamfxmlClassStudents, 'student')
        staf = ET.SubElement(jamfxmlClassTeachers, 'teacher')
        staf.text = s

    for s in studentUsernameList:
        # jamfxmlClassStudent = ET.SubElement(jamfxmlClassStudents, 'student')
        usr = ET.SubElement(jamfxmlClassStudents, "student")
        usr.text = s

    ###################################
    # WRITE XML data for Jamf
    ###################################
    print("xml file assembled, printing it below")
    jamfData = ET.tostring(jamfXMLData, encoding="unicode")
    print(jamfData)
    jamfFile = open("currentclasses/" + classXMLFileName, "w")
    jamfFile.write(jamfData)

    # Call upload_to_jamf function and pass data
    print ("Sending to jamf now")
    upload_to_jamf(classNameSanitised, className, jamfData, npKnownClassList)