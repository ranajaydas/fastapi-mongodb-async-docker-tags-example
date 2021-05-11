![](./logo.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://www.travis-ci.com/ranajaydas/fastapi-mongodb-async-docker-tags-example.svg?branch=main)](https://www.travis-ci.com/ranajaydas/fastapi-mongodb-async-docker-tags-example)
[![codecov](https://codecov.io/gh/ranajaydas/fastapi-mongodb-async-docker-tags-example/branch/main/graph/badge.svg)](https://codecov.io/gh/ranajaydas/fastapi-mongodb-async-docker-tags-example)

# What is this?
A simple REST API example using [**FastAPI**](https://fastapi.tiangolo.com/), async [**MongoDB**](https://www.mongodb.com/) & [**Docker**](https://www.docker.com/), featuring a full test suite and support for tags.

## How to launch the app
1. [Install Docker](https://www.docker.com/products/docker-desktop) on your machine.
2. Download this repo.
3. Create a `.env` file with the following variables (you can also use the `.env.example` file):
    ```properties 
    MONGO_INITDB_ROOT_USERNAME=YourUserName
    MONGO_INITDB_ROOT_PASSWORD=YourPassword
    MONGO_HOST=db
    MONGO_PORT=27017
    ```

4. Open a command line in this directory and run the following command:
    ```bash
    docker-compose up
    ```        

5. That's all! You can now navigate to [http://localhost:8000/v1/article](http://localhost:8000/v1/article) to see the REST API in action!

## How to test the API endpoints manually
1. [Install Postman](https://www.postman.com/downloads/) on your machine.
2. Import the collection **post_collection.json**.
3. Test out the different endpoints inside the collection.

## How to run automated tests
Testing is really easy thanks to [**pytest**](https://pytest.org)!
1. Open a command line in this directory and run the following command:
    ```bash
    docker-compose exec web pytest -v
    ```
2. The tests have been designed to provide 100% code coverage. 
3. After running a test, [**pytest-cov**](https://pytest-cov.readthedocs.io/en/latest/readme.html) generates a coverage report.
4. Get the docker container id for the FastAPI app using:
    ```bash
    docker ps
    ```
5. Copy the coverage report out using:
    ```bash
    docker cp <docker container id>:code/htmlcov/ .
    ```
6. Open the html file `htmlcov/index.html`

## How to stop the app and clean up
1. To stop the app, press `Ctrl + C` inside the command line from step 4 of **How to launch the app**.
2. To stop Docker Compose, run the following command:
    ```bash
    docker-compose down
    ```
3. List all the images for docker using:
    ```bash
    docker images
    ```
4. Remove the docker images for the FastAPI image and the MongoDB image using:
    ```bash
    docker rmi <FastAPI image id> <MongoDB image id>
    ```
5. Clean up any loose volumes using:
    ```bash
    docker volume prune
    ```

