# Syncora

A project for managing and processing data related to invoicing and document generation.

## Required Tools

To run and lint this project, you will need the following tools:

- **uv**: A Python package installer and resolver. It is used to manage dependencies and run Python scripts.
- **prek**: A git hook framework written in Rust. It is used for linting and formatting the codebase.
- **java**: Used to execute the JAR file in the projet.

## Installation

1. Install `uv` by following the instructions [here](https://github.com/astral-sh/uv).
2. Install `prek` by following the instructions [here](https://prek.j178.dev).
3. Install `java` by following the instructions [here](https://www.digitalocean.com/community/tutorials/how-to-install-java-with-apt-on-ubuntu-22-04).

## Running the Project

To run the project, use the following command from the root directory of the project:

```bash
uv run python3 src/app.py
```

## Linting the Project

To lint the project, use the following command:

```bash
prek run --all-files
```

This will run all the configured hooks (Black, Ruff, pyupgrade, and isort) to ensure the code is properly formatted and linted.

## Running Tools

To run specific tools, use the following commands:

### accdb_cli.py

```bash
PYTHONPATH=. uv run python3 ./tools/accdb_cli.py
```

## Project Structure

Here is a quick overview of the different directories in the project:

```
syncora/
├── src/                          # Contains the main source code of the project.
│   ├── classes/                  # Contains class definitions used throughout the project.
│   ├── constants/                # Contains constant values used in the project.
│   ├── controllers/              # Contains controller logic for handling business logic.
│   ├── database/                 # Contains database-related code and configurations.
│   ├── models/                   # Contains data models and schemas.
│   ├── pdf/                      # Contains code related to PDF generation and manipulation.
│   ├── routes/                   # Contains route definitions for the web application.
│   ├── utils/                    # Contains utility functions and helper code.
│   ├── app.py                    # The main application file.
│   └── ucanaccess-5.1.3-uber.jar # A JAR file used for database connectivity.
├── tests/                        # Contains test files for the project.
├── tools/                        # Contains additional tools and scripts.
│   └── accdb_cli.py              # A command-line tool for interacting with Access databases.
└── docker/                       # Contains Docker-related files and configurations.
```

- **src/**: Contains the main source code of the project.
  - **classes/**: Contains class definitions used throughout the project.
  - **constants/**: Contains constant values used in the project.
  - **controllers/**: Contains controller logic for handling business logic.
  - **database/**: Contains database-related code and configurations.
  - **models/**: Contains data models and schemas.
  - **pdf/**: Contains code related to PDF generation and manipulation.
  - **routes/**: Contains route definitions for the web application.
  - **utils/**: Contains utility functions and helper code.
  - **app.py**: The main application file.
  - **ucanaccess-5.1.3-uber.jar**: A JAR file used for database connectivity.

- **tests/**: Contains test files for the project.
- **tools/**: Contains additional tools and scripts.
  - **accdb_cli.py**: A command-line tool for interacting with Access databases.
- **docker/**: Contains Docker-related files and configurations.

## Environment Variables

To run the project, you will need to set up the following environment variables in your `.env` file:

```
API_SECRET=your_api_key
PARTY_ID=your_company_id
URL="https://api.sandbox.billit.be/v1"
DB_FILE="/path/to/your/database.accdb"
MONGO_IP="127.0.0.1"
MONGO_PORT="27017"
MONGO_USER="admin"
MONGO_PWD="secret"
MONGO_DB="facturation_test"
```

Here is an explanation of each field:

- **API_SECRET**: The API key to access the Billit Sandbox API.
- **PARTY_ID**: The company ID on Billit.
- **URL**: The base URL for the Billit Sandbox API.
- **DB_FILE**: The path to your Access database file.
- **MONGO_IP**: The IP address of your MongoDB server.
- **MONGO_PORT**: The port number for your MongoDB server.
- **MONGO_USER**: The username for your MongoDB server.
- **MONGO_PWD**: The password for your MongoDB server.
- **MONGO_DB**: The name of your MongoDB database.

Replace the placeholder values with your actual configuration details.

## Running MongoDB Container

To run the MongoDB container, use the following command:

```bash
docker run --name facturation_test --rm -e MONGODB_INITDB_ROOT_USERNAME=admin -e MONGODB_INITDB_ROOT_PASSWORD=secret mongodb/mongodb-community-server:latest
```

## Additional Information

- **Python Version**: The project requires Python 3.14 or higher.
- **Dependencies**: The project dependencies are listed in `pyproject.toml`.
- **Configuration**: The `prek.toml` file contains the configuration for the linting and formatting tools.
