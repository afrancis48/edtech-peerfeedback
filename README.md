# Peer Feedback Tool Final Project README

This tool requires a working instance of Canvas to be deployed. This means that running the tool 
on the server is imposssible without an instance of Canvas. Instead, we use Docker to deploy a local dummy
instance of Canvas.

Repo link: https://github.com/afrancis48/edtech-peerfeedback


![Python: 3.6+](https://img.shields.io/badge/python-3.6%2B-blue.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![build status](https://gitlab.com/gabrieljoel/peerfeedback-ng/badges/dev/build.svg)](https://gitlab.com/gabrieljoel/peerfeedback-ng/commits/dev)
![coverage](https://gitlab.com/gabrieljoel/peerfeedback-ng/badges/dev/coverage.svg?job=backend_test)

## Setting up Development Environment

### Pre-requisites
1. Python (3.6+)
2. Docker with [Docker Compose](https://docs.docker.com/compose/) or Docker Desktop (WSL2)
3. Node.js with [Yarn](https://yarnpkg.com/lang/en/) package manager

### Setting up development environment

1. Clone the repository or use the existing zip file submission

    ```
    git clone https://github.com/afrancis48/edtech-peerfeedback.git
    ```

2. Create a file called `.env` with the following content (This file already exists in the zip file and in the repo)

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
    docker-compose build web; docker-compose up
    ```

4. Once docker has finished building all the images, open a new terminal and execute the db setup script. This will populate the database and run yarn serve to deploy the frontend.

    ```shell
   ./db_setup.sh
    ```
5. Navigate to localhost:4000/app/home

6. Login as teacher user or student user:

Teacher: 

Username `canvas@example.edu` Password `canvas-docker`

Student:

Username `student0@example.edu` Password `secure123`

To switch between users:
- Navigate to the Canvas instance at localhost:3000
- Sign out of existing user
- Sign in as the user you want

