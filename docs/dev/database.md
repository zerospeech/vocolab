
# Zerospeech API - Databases

Here we have the basic layout of the Databases & disk data of the API.


## Database Structure


The database used for users & challenges is SQLITE with an async connector.


### Tools 

For the connector we use [databases package](https://www.encode.io/databases/)
which is an [SQLAlchemy Core](https://docs.sqlalchemy.org/en/14/core/) compactible
 wrapper around the [aiosqlite](https://aiosqlite.omnilib.dev/en/stable/) connector.


### Configuration

The only configuration needed for databases to operate is the `Settings.DATA_FOLDER`
to be set to an existing directory and have write permissions, if the `zerospeech.db` 
file does not exist it is created with all the empty tables at API startup.

see [connect config](../zerospeech/db/base.py)
and [api startup](../zerospeech/api/main.py)


### Schema 

The schema of the database is declared in the [zerospeech.db.schema](../zerospeech/db/schema)
module. Tables are declared using basic [SQLAlchemy](https://docs.sqlalchemy.org/en/14/core/) Core Syntax
and mapped to a [Pydantic](https://pydantic-docs.helpmanual.io) dataclass for 
validation and easier manipulation.


### Tables


#### Auth

- **users_credentials**: Table containing all users and their auth credentials.

> *Any sensitive information is hashed & salted

- **logged_users**: Table containing all active user sessions & their tokens.

- **password_reset_users**: Table containing all password reset sessions.


#### Challenges

- **challenges**: Table containing all registered challenges.

- **challenge_submissions**: Table containing all submissions uploaded to the challenges

- **evaluators**: Table containing all registered evaluation functions for the submissions.


### Queries

All queries & interactions with the database is in the [zerospeech.db.q](../zerospeech/db/q) module.
Queries are in async functions using [SQLAlchemy](https://docs.sqlalchemy.org/en/14/core/) Core Queriyng language. 

## Disk Data


All file data is saved in a folder configured as `Settings.DATA_FOLDER`.


### User profile data

User profile data is stored as a json file at `Settings.USER_DATA_DIR / <username>.json`.


### Submission data

Submissions are uploaded as zip files containing various files used to calculate 
a score. All files relative to each submission is stored at :

`Settings.SUBMISSION_DIR / <submission_id> `


### Static files


Static files are served in the API under the path : `<api-url>/static/<path>`

And are stored in : `Settings.DATA_FOLDER / _static `


### Template Files 


Template files are used for api HTML responses, email notifications, mattermost notifications.

They are created using [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/) Templating language, 
and are stored in the [zerospeech.templates](../zerospeech/templates) module.
