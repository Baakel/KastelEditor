# KastelEditor
Webpage that allows users to streamline the process of creating a new project compliant with the [KASTEL competence center](https://www.kastel.kit.edu/) guide lines.

## Getting Started
To download the website simply click on the download link on github or run `git clone https://github.com/Baakel/KastelEditor.git` on your bash terminal.

### Prerequisites
To run this server you need a computer running python 3.5 or later and Docker-CE 18.09 or later.
These can be found here 
You will also need the following packages installed [Requirements](requirements.txt)

### Installing
after downloading, simply `cd` into the **KastelEditor** directory and run the command `docker-compose up -d`. The first time it will build the KastelEditor app image and it will download the mysql image.
This will also create the db volume.

## Usage
To start the server you need to `cd` into the **KastelEditor** directory and run the `docker-compose up -d`. Your port _**5000**_ needs to be free for this to run.
To access the server simpply go to http://localhost:5000/
To stop the server run the `docker-compose down` command. This will stop all active containers and remove them. The database volume will not be removed this way.
If you change anything in the codebase you will need to rebuild the **KastelEditor Image**, to do this run `docker-compose build`.

If you do any changes to the models of the database you need to migrate them before rebuilding the image.
To do this run `export FLASK_APP=kastel.py` and then run `flask db migrate` 

## Deployment
_TODO_

## Built With
- [Python 3.5](https://www.python.org/) - Language used
- [Flask](http://flask.pocoo.org/) - Web framework used
- [Docker](https://www.docker.com/) - Container Engine
- [SQLite](https://www.sqlite.org/index.html) - Database used locally to test
- [MySQL](https://www.mysql.com/) - Database used inside the container
