# Peer Feedback platform for OMSCS

![Python: 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![build status](https://gitlab.com/gabrieljoel/peerfeedback-ng/badges/dev/build.svg)](https://gitlab.com/gabrieljoel/peerfeedback-ng/commits/dev)
![coverage](https://gitlab.com/gabrieljoel/peerfeedback-ng/badges/dev/coverage.svg?job=backend_test)

## Setting up Development Environment

### Pre-requisites

1. Docker with [Docker Compose](https://docs.docker.com/compose/)
2. Node.js with [Yarn](https://yarnpkg.com/lang/en/) package manager

### Setting up development environment

1. Clone the repository

    ```
    git clone git@gitlab.com:gabrieljoel/peerfeedback-ng.git
    cd peerfeedback-ng
    ```

2. Create a file called `.env` with the following content

    ```properties
    PEERFEEDBACK_SECRET=<your_really_long_secret_key>
    PORT=5000
    ENV=dev
    PYTHONUNBUFFERED=0
    WDB_SOCKET_SERVER=wdb
    WDB_NO_BROWSER_AUTO_OPEN=True
    CANVAS_API_URL=http://canvas:3000/api/v1/
    CANVAS_API_KEY=canvas-docker
    AUTHLIB_INSECURE_TRANSPORT=1
    FLASK_DEBUG=True
    FLASK_APP=autoapp.py
    CANVAS_ACCESS_TOKEN_URL=http://canvas:3000/login/oauth2/token
    CANVAS_AUTHORIZE_URL=http://localhost:3000/login/oauth2/auth
    CANVAS_CONSUMER_KEY=10000000000001
    CANVAS_CONSUMER_SECRET=test_developer_key
    SENDGRID_API_KEY=<sengrid_api_key>
    SEND_NOTIFICATION_EMAILS=False
    REDIS_URL=redis://redis:6379
    # open only when running pytest tests
    # DATABASE_URL=postgresql://docker:docker@db:5432/testdb
    ```

3. To get the app running run
    ```shell
    docker-compose up
    ```

4. Once docker has finished building all the images, initialize the db
    ```shell
    docker exec -it peerfeedback-ng_web_1 bash  # login to the app container
    flask db upgrade                            # initialize the db with schema
    ```

5. Now the app can be accessed at [http://localhost:5000](http://localhost:5000)

For the structure of the application, the files and their purpose, refer to the
[Contributing Guide](./CONTRIBUTING.md)

### Developing Frontend

If you want to set up the development environment for frontend, open a new terminal and run:

```shell
cd peerfeedback-ng/frontend
yarn install
yarn serve
```
This starts the frontend development server at http://localhost:4000 with live reload and
proxy of API calls to the backend at port 5000.

### Adding Sample Data for development

In order to effectively test the application, you will need course and assignment information
with students enrolled to the class and TAs assigned to the course.
The following set of commands will generate a course with 3 assignments
and the given number of students with all the first assignment submitted
for all the students, the second assignment submitted only by some students
and the given number of TAs.

```shell
docker exec -it peerfeedback-ng_web_1 bash  # login to docker container
flask init-canvas --students 73 --tas 7     # change the student and TA count as required
flask add-rubric                            # adds a test rubric to the DB
exit                                        # logout of the docker container
```

## Deployment

### Optimizing the frontend

While using `yarn serve`

Go to [http://127.0.0.1:8888](http://127.0.0.1:8888). This opens the Webpack
Analyzer infographic in the browser. Check for sizes of the libraries used and trim where necessary

### To deploy in Heroku

```shell
git push heroku master
```

In your production environment, make sure the `FLASK_DEBUG` environment variable is unset or is set to `0`, so that `ProdConfig` is used.

## Testing

The app contains multiple test suites focusing on different areas of the application as detailed below:

| Test Area         |  Kind            |  Language       | Test Framework    | Gitlab CI Autorun |  Coverage  |
|-------------------|------------------|-----------------|-------------------|-------------------|------------|
| Backend Flask App | Unit Test        | Python          | pytest            |  ✔                |  ![coverage](https://gitlab.com/gabrieljoel/peerfeedback-ng/badges/dev/coverage.svg?job=backend_test) |
| Frontend Vue App  | Unit Test        | JS              | Mocha + Chai      |  ✔                |  NA        |
| Browser           | E2E              | JS              | TestCafe          |  ✘                |  NA         |

### Running tests

#### 1. Backend Tests

The tests for the backend application lives in the `tests` folder and requires a test database to be setup in order to run.
In the docker based development setup, login to the db container and create the test db:

**Note:** The above setup needs to be done only once
```
docker exec -it peerfeedback-ng_db_1 bash  # login to docker container
psql -w docker -U docker
# in the psql prompt
CREATE DATABASE testdb;
GRANT ALL PRIVILEGES ON DATABASE testdb TO docker;
\q  # exit psql
exit # exit docker container
```

Now run the tests:

```
pytest  tests
```

#### 2. Frontend tests

The frontend tests are in the `frontend/tests/unit` directory. To run the tests:

```
cd frontend
yarn test:unit
```

#### 3. End to End tests

End to End tests are browser based and the test command requires **Firefox** browser for running.

```
cd frontend
yarn test:e2e
```

If you need to use a different browser then edit the `test:e2e` command in `frontend/package.json`
to suit your browser. Refer the [testcafe docs](https://devexpress.github.io/testcafe/documentation/using-testcafe/common-concepts/browsers/browser-support.html)
for more information about browser support.

## Linting

We use [Black](https://github.com/ambv/black) to format our code. To lint the entire project run:

    black peerfeedback

## Migrations

Whenever there are change in models and a DB migration needs to be generated,
run the following command:

    flask db migrate -m "Adds new column for some model"

This will auto-generate a migration file. Since the DB server is a docker container
the DB has to be updated from within the container. Run:

    docker exec -it peerfeedback-ng_web_1 bash     # login to docker container
    flask db upgrade

For a full migration command reference, run `flask db --help`.

To drop the entire db, run `flask shell` inside the docker container and then:

```
db.reflect()
db.drop_all()
```

## Canvas

Once the `docker-compose up` command is run, a local version of Canvas LMS
will be available at http://localhost:3000/

Login as the Administrator using the following credentials

Username `canvas@example.edu` Password `canvas-docker`

To delete all data in the Canvas docker volume use the following:

`docker rm -v containername`

## Managing Docker Containers

To SSH into a Docker container use the following:

```shell
docker exec -it peerfeedback_db_1 /bin/bash
```

To build a container use the following:

```shell
docker-compose build web
```

## Database Dumps

### Export a DB dump to Heroku

- Create dump ``pg_dump -h db -U docker --format=c db_name > db_file.dump`` 
- Copy to host machine ``docker cp 189241be63ff:/opt/db_file.dump`` 
- Upload to S3
- Restore to Heroku ``pg:backups:restore 'https://s3.amazonaws.com/pf-store/pf.dump' DATABASE_URL --app peerfeedback``

### Create a DB dump from a DB running on Heroku

- Create backup ``heroku pg:backups capture``
- Get download URL ``heroku pg:backups public-url``
- Download ``wget -O peerfeedback.dump <url>``
- Copy the dump into the DB container 
``docker cp peerfeedback.dump 5e9f4ce6bf0f:/opt/peerfeedback.dump``
- SSH into DB container ``docker exec -it peerfeedback_db_1 /bin/bash``
- Restore 
``pg_restore -U docker --verbose --clean --no-acl --no-owner -h localhost -d peerfeedback peerfeedback.dump``

## Debugging

Where you want to debug the code, add the following lines:
```py
import wdb
wdb.set_trace()
```

To see which debugging session are currently open, open your browser at
http://localhost:1984/

For `printf` debugging use the following

```py
import sys
print('Hello world!', file=sys.stderr)
```

## Managing Python Dependencies
Python dependencies are specified on the `requirements.in` file. This file must be compiled into a `requirements.txt` file for use by Pip. To compile the `requirements.in` file use the following:

```shell
pip-compile --upgrade requirements.in --output-file requirements.txt
```

Please beware of potential new bugs introduced by newer versions of packages.
