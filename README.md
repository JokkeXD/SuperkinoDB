# PWP SPRING 2024
# SuperkinoDB
# Group information
* Joona Kontiokoski, joona.kontiokoski@student.oulu.fi
* Jukka Vaulanen, jukka.vaulanen@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

## Environment setup
Clone the repository to the machine. This project setup expects that Python3 is installed.

### Create virtual environment
Create a Python virtual environment for the repository.
```
python3 -m venv venv
```

### Activate virtual environment
Linux/MacOS:
```
source venv/bin/activate
```
Windows:
```
venv\scripts\activate.bat
```
Powershell:
```
venv\scripts\Activate.ps1
```
Virtual environment can be deactiavated with:
```
deactivate
```

### Installing dependencies
Install required packages inside your virtual environment:
```
pip install -r requirements.txt
```

## Project setup
Before running the project, the database needs to be created and initialized.
SuperkinoDB uses SQLite3 database. It can be initialized with built-in Flask
click commands. Optionally, the database can also be populated with test data.
### Create database
```
flask --app superkinodb init-db
```
### Populate with test data
```
flask --app superkinodb testgen
```

## Run the project
```
flask --app superkinodb run
```

## Testing
### Make the project importable for testing
```
pip install -e
```
__TBD__

## Developing the project
### Linter
Use PyLint with the following options to check that the code follows the coding
standard of the project:
```
pylint superkinodb --disable=no-member,import-outside-toplevel,no-self-use
```
__TBD__
