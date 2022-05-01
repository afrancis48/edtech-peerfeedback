# Contribution Guide

This document is intended to serve as the comprehensive guide to understanding the structure of this project, the different pieces and to ease a new developer into the code base.

## Table of contents

1. [Overview](#overview)
    - [Canvas LMS](#canvas-lms)
2. [Structure of the project](#structure-of-the-project)
    - [Setting up the development environment](#setting-up-the-development-environment)
3. [Flask Backend](#flask-backend)
4. [Vue Frontend](#vue-frontend)
5. [Version Control](#version-control)
6. [First Steps in Contributing](#first-steps-in-contributing)
    - [Adding a feature to the backend](#adding-a-feature-to-the-backend)
    - [Adding a feature to the frontend](#adding-a-feature-to-the-frontend)

## Overview

The application's development is modularized into frontend and backend separately. The backend is a Flask application serving a
REST-like API, and the frontend is a Vue JS single page application. It is modularized in a way, the functionality of the two
 can be developed independently.

Getting the source code:

```
git clone https://gitlab.com/gabrieljoel/peerfeedback-ng.git
```

### Canvas LMS

This application is like a consumer application of the [Canvas LMS](https://www.canvaslms.com/). The application depends heavily
on the [Canvas API](https://canvas.instructure.com/doc/api/) for all its data. While most of the data related to student feedback,
pairing, grading ..etc., are completely Peer Feedback specific, all the underlying data, like courses, assignments, users, and submissions
are completely dependent on the Canvas API.

The PeerFeedback is a hybrid application. It consumes data from Canvas via Canvas REST API, it also has its own local data and provides it
through its own REST like API.


## Structure of the project

```
.
├── .dockerignore
├── .gitignore
├── .gitlab-ci.yml
├── CONTRIBUTING.md
├── Dockerfile.db
├── Dockerfile.web
├── LICENSE
├── Procfile
├── README.md
├── assets
├── autoapp.py
├── docker-compose.yml
├── gunicorn_config.py
├── migrations
├── package.json
├── peerfeedback
├── requirements.in
├── requirements.txt
├── runtime.txt
└── tests
```

There are four folders at the first level of the project:

1. `frontend` - this houses the Vue frontend application and the entire Node JS related development files.
2. `migrations` - this contains the Alembic database migration scripts for the backend flask application
3. `peerfeedback` - this contains the backend Flask application
4. `tests` - this contains the unit tests for the Flask application

The important files in the root directory of the project:

1. `.dockerignore` - file notifies the locations that shouldn't be copied over when the docker containers are loaded
2. `.gitignore` - Git-ignore file
3. `.gitlab-ci.yml` - defines the Continuous Integration (CI) setup that would run the unit tests at every push to Gitlab
4. `autoapp.py` - the python file which creates and runs the Flask app
5. `docker-compose.yml` - the docker-compose file defining the docker setup required for development
6. `Dockerfile.db` & `Dockerfile.web` - Docker files for setting up the DB and the Flask app (web) containers
7. `gunicorn_config.py` - the gunicorn configuration used in the Flask web container
8. `package.json` - the node identifier file that serves as the entry point for Gitlab CI to run the frontend tests
9. `Procfile` - Heroku configuration file which outlines the services to run
10. `requirements.in` - human readable list of Flask app's dependencies
12. `requirements.txt` - machine-readable list of Flask app's dependencies
13. `runtime.txt` - file defining the Python runtime for Heroku

### Setting up the development environment

The steps to setup the development environment and the various related things are outlined in the [README](README.md) file.
Kindly read the README file to setup your development environment and ensure you have an working instance of the application.

## Flask Backend

The Flask backend is spread across the three folders `peerfeedback`, `migrations` and `tests`. You will be editing files only
from the folders `peerfeedback` and `tests`. The `migrations` folder holds the Alembic database migration scripts and won't need any developer
interference unless the developer knows exactly what he/she is doing.

Directory structure of `peeerfeedback`:

```
.
├── __init__.py
├── admin
├── api
├── app.py
├── commands.py
├── crons.py
├── database.py
├── exceptions.py
├── extensions.py
├── public
├── settings.py
├── static
├── templates
├── user
└── utils.py
```

The application is organized into blueprints. Below is a list of folders and their contents:

1. `admin` - contains the blueprint which deals with the `Flask-Admin` related views
2. `api` - contains the blueprint which has the REST like API endpoints. This blueprint serves almost all the information required by frontend.
3. `public` - contains the endpoints which will server all the static content for the frontend
4. `static` - static folder of the application, contains all the static files like CSS, JS and images
5. `templates` - templates folder of the Flask application
6. `user` - contains the blueprint which deals with user related endpoints like login, OAuth validation, JWT Tokens..etc,

Refer to the documentation in the files and functions for their specific uses.

## Vue Frontend

The frontend is a Vue JS application created and maintained using the Vue-Cli 3.x and uses **yarn** as the package manager.

The directory structure and the explanation of the files within is given below:

```
.
├── babel.config.js
├── package.json
├── public
├── src
│   ├── App.vue
│   ├── api
│   ├── assets
│   ├── components
│   ├── main.js
│   ├── registerServiceWorker.js
│   ├── router.js
│   ├── store
│   ├── utils
│   └── views
├── tests
│   ├── e2e
│   └── unit
├── vue.config.js
└── yarn.lock
```

1. `babel.config.js` - Babel transpiler config file
2. `package.json` - Node build system package file. Contains the dependencies and commands to run the application
3. `public` - folder generated by the Vue-Cli build system to house the starter HTML and related files.
4. `src` - folder where all the source code and files go.
    - `App.vue` - Vue component defining the Vue application skeleton
    - `api` - Collection of JS files which form the API layer of the application. This module handles all the API
      communication using the `axios` library.
    - `assets` - contains any custom css/scss files, svg files or images which would be referenced by the Vue components
    - `components` - Vue components built for specific purposes
    - `main.js` - the main entry point defining the `Vue()` instance and the plugins
    - `registerServiceWorker.js` - service worker for PWA generated by Vue CLI
    - `router.js` - Vue-Router outlining the routes of the frontend application and the corresponding components
    - `store` - The Vuex store which holds the state of the application. The store is a collection of Vuex modules
       structured the same way as the `api` module.
    - `utils` - Module which has the utility functions that might be shared across the application
    - `views` - contains the Vue components that can be described as the **page** of the application.
5. `tests` - folder containing the unit tests and E2E tests for the application
6. `vue.config.js` - the Vue-Cli config file
7. `yarn.lock` - Yarn package manager's lock file

## Version Control

Git is the VCS used for the application. The source code management is modelled on [this strategy](https://nvie.com/posts/a-successful-git-branching-model/).
It is strongly suggested to read the post to understand the strategy in depth. Here are the key points:

1. The main development is carried out in the `dev` branch. **IMPORTANT** Always do a `git checkout dev` before editing the files.
   ```
   git commit -am 'fixed #xxx now things are better'
   git push origin dev
   ```
2. Once a feature is ready and available for testing by other, then the `dev` branch is merged into the `staging` branch. This automatically
   triggers the CI to test the application and deploy it to the *staging* server in Heroku if the tests pass without any issue.
   **Note:** Check with the project maintainer (@gabrieljoel) about the availability of the staging server. When this guide was written,
   the test Canvas server was out of function and the staging server wasn't being put to use.
   ```
   git checkout staging
   git merge -no-ff dev
   # Always use the -no-ff flag to create seperate merge commits and keep the git tree clean
   ```
3. Sometimes new branches are created from the `master` branch to create hotfixes for production bugs. Those branches are merged to both
   the `master` and `dev` to synchronize changes.
   ```
   git checkout master
   git branch hotfix-bug-9999
   git checkout hotfix-bug-9999
   # Edit some files and ceate the bug fix
   git commit -am 'hotfix for bug 9999'

   # Now synchronize the change in both master and dev
   git checkout master
   git merge -no-ff hotfix-bug-9999  # always use no-ff when merging
   git push origin master
   git checkout dev
   git merge -no-ff hotfix-bug-9999
   git push origin dev
   ```

## First Steps in Contributing

1. Clone the repository
2. Switch to the `dev` branch
3. Follow the *Setting Up Development Environment* instructions from the [README](README.md) and get a working dev environment ready

### Adding a feature to the backend

* The changes to the backend goes into the `peerfeedback` Python package.
* Unless it is a admin functionality of some user management issue, the work would go mostly into the `api` folder
* The API is spread across the following files:
    - `__init__.py` - exposes the `views.py` for easier import by other modules
    - `errors.py` - Defines the error strings and exceptions that would be raised and returned by the api
    - `jobs.py` - holds all the Python-RQ jobs that would be run in the background, which are considered too slow
        for one request-response cycle, like creating pairings, sending emails, giving medals ..etc.,
    - `models.py` - these define the SQLAlchemy models that define the tables in the database
    - `resource.py` - defines the [Flask-Restful](https://flask-restful.readthedocs.io/en/latest/) resources which provide
        quick ways to define CRUD endpoints for the models
    - `schemas.py` - defines the [marshmallow](https://marshmallow.readthedocs.io/) schemas which are used for serialization
        of the data models into JSON
    - `utils.py` - utility functions used across the API files
    - `views.py` - the api endpoint definitions (Flask `route` functions)
* Make the necessary changes in the files and test the feature
* Run the backend tests as described in the [README](README.md#1-backend-tests) to ensure no regression. **Note:** Even if
  you miss running the tests, the Gitlab CI is set to run the tests with every push and would let you know about the regression.
* Lint the code using Black. It is just `black peerfeedback`
* Commit and push


### Adding a feature to the frontend

* The frontend source code lives in the directory `frontend/src`
* Open a new terminal. Move to `peerfeedback-ng/frontend` and run `yarn serve` to start the live server instance which would
  compile and serve you the latest version of the frontend application as you edit.
* The location to look for the files depends on the type of issue you are working on:
    1. Change in backend API URL patters - `src/api`
    2. UI/UX changes - `src/components`
    3. Change in frontend navigation and routes - `src/router.js` and the corresponding pages are in `src/views`
    4. Adding new Vue Plugin to the app - `yarn add <vue plugin>` and then include it in `src/main.js`
    5. Changes to the application state data (Vuex changes) - `src/store`
* The app is made of three layers:
    1. At the bottom is the API layer dealing with the communication between the backend the frontend. `src/api`
    2. At the middle is the State layer dealing with the data (state) that is handled by the UI. `src/store` and `src/router.js`
    3. At the top is the UI layer dealing with the presentation and user interaction. `src/views` and `src/components`
* Based on the issue you are working with, you might have to work across all layers, which means editing files in three directories,
  or just a single layer. Make the necessary changes to fix the issue.
* Run the frontend tests as described in the [README](README.md#2-frontend-tests) to ensure no regression. Again, Gitlab CI will do
  it for you, if you miss it.
* Lint the code using `yarn lint`
* Commit and push
