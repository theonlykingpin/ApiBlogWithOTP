# Django REST Framework Blog Api
## With one time password and two steps login

## Features

- Authentication with phone number and OTP code to user's phone.
- Two-step verification for authentication.
- Using cache to temporarily store otp code.
- Generate tokens using simple-jwt after authentication.
- Production-ready configurations
- Automatically delete photos after deleting the blog.
- Ability to comment on blogs.


## Technologies

- [Python 3.9](https://www.python.org/) - [Django 3.2](https://docs.djangoproject.com/en/3.2/releases/3.2/) - [Django Rest Framework 3.12](https://www.django-rest-framework.org/) - [Nginx](https://www.nginx.com/) - [Docker](https://www.docker.com/) - [PostgreSQL](https://www.postgresql.org/) - [Gunicorn](https://gunicorn.org/)


## Installation

**Clone the project**

```shell
git clone https://github.com/theonlykingpin/drf_blog_api.git && cd drf_blog_api && cp .env-sample .env && cp .env.db-example .env.db && rm .env-sample .env.db-example
```


Please enter the required information in the **.env** and **.env.db** files before running the project.


**Run project**

**create docker network**

```shell
docker network create nginx_network1
docker network create blog_network
```

**create docker volume**

```shell
docker volume create db_data
```

**run project**

```shell
docker-compose up -d
```


## LICENSE

see the [LICENSE](https://github.com/amirpsd/drf_blog_api/blob/main/LICENSE) file for details. based on another open source project.
