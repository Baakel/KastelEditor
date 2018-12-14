FROM python:3.6-alpine

RUN adduser -D kastel

WORKDIR /home/kastel

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn
RUN venv/bin/pip install -Iv pymysql==0.8.1

COPY editorapp editorapp
COPY db_repository db_repository
COPY migrations migrations
COPY config.py README.md app.db run.py tests.py boot.sh kastel.py ./
RUN chmod a+x boot.sh

ENV FLASK_APP kastel.py

RUN chown -R kastel:kastel ./
USER kastel

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
