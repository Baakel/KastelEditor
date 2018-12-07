# KastelEditor
Webpage that allows users to streamline the process of creating a new project compliant with the [KASTEL competence center](https://www.kastel.kit.edu/) guide lines.

## Getting Started
To download the website simply click on the download link on github or run `git clone https://github.com/Baakel/KastelEditor.git` on your bash terminal.

### Prerequisites
To run this server you need a computer running python 3.5 or latter.
You will also need the following packages installed [Requirements](requirements.txt)

### Installing
To set up your database run the `db_create.py` file.

## Usage
To start the server run the `run.py` file. Your port 5000 needs to be free for this to run. After that you can connect to the server from *localhost:5000* 
You will need to log in using your Github account.
If you are using the docker image then the command to start it would be `docker run -p 5000:5000 --rm kasteleditor:latest`

## Deployment
_TODO_

## Built With
- [Python 3.5](https://www.python.org/) - Language used
- [Flask](http://flask.pocoo.org/) - Web framework used
- [SQLite](https://www.sqlite.org/index.html) - Database used
