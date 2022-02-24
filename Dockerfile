FROM python:3.9-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./src /src
COPY ./requirements /requirements
WORKDIR /src

RUN pip install --upgrade pip && pip install -r /requirements/requirements.txt

CMD python3 manage.py makemigrations --noinput && \
    python3 manage.py migrate --noinput && \
    python3 manage.py collectstatic --noinput && \
    gunicorn -b 0.0.0.0:8000 config.wsgi
