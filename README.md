# KastelEditor
Webpage that allows users to streamline the process of creating a new project compliant with the [KASTEL competence center](https://www.kastel.kit.edu/) guide lines.

## Getting Started
To download the website simply click on the download link on github or run `git clone https://github.com/Baakel/KastelEditor.git` on your bash terminal.

### Prerequisites
To run this server you need a computer running python 3.5 or latter.
You will also need the following packages installed _(They can also be found in the requirements.txt doc)_
- Flask_WTF >= 0.14.2
- Flask_SQLAlchemy >= 2.3.2
- Flask_Login >= 0.4.1
- SQLAlchemy >= 1.1.15
- Flask >= 0.12.1
- GitHub_Flask >= 3.2.0
- requests >= 2.9.1
- flask_github >= 0.1.3
- sqlalchemy_migrate >= 0.11.0

### Installing
To set up your database run the `db_create.py` file.

## Usage
To start the server run the `run.py` file. Your port 5000 needs to be free for this to run. After that you can connect to the server from *localhost:5000*. You will need to log in using your Github account.

## Deployment
_TODO_

## Built With
- [Python 3.5](https://www.python.org/) - Language used
- [Flask](http://flask.pocoo.org/) - Web framework used
- [SQLite](https://www.sqlite.org/index.html) - Database used
