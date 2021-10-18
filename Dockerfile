FROM python:2.7
LABEL maintainer="Boram Gwon"

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN python init_db.py

# command to run on container start
CMD [ "python", "app.py" ]
