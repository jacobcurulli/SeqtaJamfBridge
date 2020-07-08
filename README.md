# SeqtaJamfBridge
 
This script will connect to a SEQTA database and extract data from an approved_classes.csv file. Then the data is formatted for Jamf Pro Classes and uploaded. 

### Known Issues

Thing that don't work yet

```
Including a class with no teachers and/or students will result in processing stopping at that class.
A future update will account for this
```


### Prerequisites

What do you need to get this working

```
Read only access to the SEQTA server. You will need to contact SEQTA support for this.
Python 3.8
Required Python packages
	- psycopg2
	- configparser
	- ElementTree
	- csv
	- configparser
	- requests
	- datetime
	- numpy
Jamf Pro
```

### Installing

```
The approved_classes.csv file needs to include the names of each class that you want to extract data for. 
The class name is checked against the 'name' value in the 'classunit' table. It will generally be something like 2020.09DRA#1
If you check a teacher timetable and look at the class name in the top left of the timetable view you will see the class name.

You need to rename the example.config.ini file to config.ini and put in the correct database credentials

I wanted to have one extra teacher account on all of the classes so that they coud be easily managed.
In the config file you can declare this teacher account - it must be an account on the Jamf Pro server or an existing teacher account.


```

## Versioning

I use [SemVer](http://semver.org/) for versioning.

## Authors

* **Jacob Curulli** - *Author* - [website](https://www.jacobcurulli.com)

## License

This project is licensed under the CC 4.0 - see the [License.md](License.md) file for details

## Acknowledgments

*
