# VocoLab Administration

The VocoLab platform can be administrated using a CLI interface, using the command `voco`. 

To see all the available commands you can type `voco help`. 

> For the docker installation the command needs to run inside the docker `docker-compose exec api voco help`.

Below you can find all the available commands and their documentation. All the commands are layered in a tree
schema to allow subcommands. All commands and subcommands accept the `-h/--help` option to 
show a description of arguments & function. 

```
list of available commands : 

.
├── api:	 Command for api instance administration 
│   ├── config:	 API Deployment config files 
│   │   ├── gunicorn:	 Generate a template gunicorn config file 
│   │   ├── nginx:	 Generate a template Nginx server file 
│   │   ├── service:	 Generate a template SystemD unit file to manage api daemon 
│   │   └── socket:	 Generate a template SystemD socket unit file 
│   ├── init:	 Initialise components needed for the API 
│   └── serve:	 Run debug instance of API using uvicorn 
├── challenges:	 Command for challenge administration (default: list)
│   ├── add:	 Command to create new challenges 
│   └── set:	 Command to alter properties of Challenges
├── evaluators:	 Container for evaluator functions manipulation 
│   ├── args:	Update base arguments of an evaluator 
│   ├── discover:	 Command to list all challenges
│   └── hosts:	 Command to list all hosts containing evaluators 
├── leaderboards:	 Administrate Leaderboard entries (default: list)
│   ├── build:	 Compile entries into the leaderboard 
│   ├── create:	 Create a new leaderboard entry 
│   ├── edit:	 Edit Leaderboard entries 
│   └── show:	 Print final leaderboard object 
├── messaging:	 Custom Message Command
│   ├── echo:	 Send an echo message 
│   └── update:	 Send an update message 
├── settings:	 Commands managing settings 
│   └── template:	 Generate a template .env file 
├── submissions:	 List submissions 
│   ├── archive:	 Archive submissions 
│   ├── author_label:	 Update or set the author_label of a submission 
│   ├── create:	 Adds a submission 
│   ├── delete:	 Deletes a submission 
│   ├── eval:	 Launches the evaluation of a submission 
│   ├── evaluator:	 Update or set the evaluator of a submission
│   ├── fetch:	 Fetch submission from a remote server (uses rsync) 
│   ├── status:	 Set submission status 
│   └── upload:	 Upload a submission to a remote server (uses rsync) 
├── test:	 Administrate Task Workers 
│   ├── debug:	 Test things as cmd 
│   └── email:	 Send an email to test SMTP Parameters 
├── users:	 Command for user administration (default: list)
│   ├── activate:	 User activation/deactivation 
│   ├── create:	 Create new users 
│   ├── delete:	 Delete a user
│   ├── notify:	 Notify all users 
│   ├── password:	Password reset sessions 
│   │   ├── check:	 Check the password of a user 
│   │   └── reset:	 Check the list of reset sessions 
│   ├── sessions:	 List logged users 
│   │   ├── close:	 Close user sessions 
│   │   └── create:	 Create a session for a user 
│   └── verify:	 User verification 
└── worker:	 Administrate Task Workers 
    ├── generate:	 Generate files allowing to configure workers
    │   ├── settings:	 Generate a template systemD unit file to manage workers daemon 
    │   └── systemD:	 Generate a template systemD unit file to manage workers daemon 
    └── test_echo:	 Send a test message to the echo worker server 

```

## `voco users`

Command, allowing to manipulate & administrate users.

The base command allows listing existing users.

#### `voco users:create`

Creating users can be done using the API ([api.example.com/page/new-user](api.example.com/page/new-user)), or
using the CLI.

> Fields : First Name, Last Name, Email, Affiliation, Password

An option exists that allows mass importation of users from a json file `voco users:create -f samples/users.json`

#### `voco users:verify`

User verification is usually done via a URL sent via email to the user upon account creation. 
This command allows the admin to :

* resend verification email to user: `voco users:verify --send <UID>`
* massively resend verification email to all unverified users : `voco users:verify --send-all`
* manually force verification of a user : `voco users:verify --verify <UID>`
* mark all unverified users as verified : `voco users:verify --verify-all`

#### `voco users:activate`

Allows activation and deactivation of users (prevents login upload and other interactions with API)

#### `voco users:delete`

Allows deletions of a user 

> !! WARNING this action removes all submissions & leaderboard entries user `--save <PATH>` to export data before deletion.

#### `voco users:password`

Allows manipulation of users passwords :

* `voco users:password:check <UID>`: allows checking a password against 
* `voco users:password:reset <UID>`: reset a user's password by creating a reset session and sending the user an email.
* `voco users:password:reset:sessions`: manipulate active password reset sessions (show/clean)

#### `voco users:sessions`

Manipulate/list user sessions, root command allows listing active sessions

* `voco users:sessions:close -u <UID>` close a user session
* `voco users:sessions:close --close-all` close all user sessions
* `voco users:sessions:create <UID>` create a session for a user (prints the token to be used)

## `voco challenges`

A subcommand allowing to manipulate challenge data.
Root command allows listing registered challenges.

#### `voco challenges:add`

Allows to create a new challenge.

> Fields: Label, URL (link to the website with info), start date (dd/mm/yyyy) , end date (Optional)

An `-f <file.json>` allows importing multiple challenges from a json file.

#### `voco challenges:set`

Allows to alter the value of an attribute of a challenge.

Ex :

* `voco challenges:set <ID> active false`
* `voco challenges:set <ID> end_date 02/02/2025`

## `voco evaluators`

Allows to manipulate evaluators.
Root command allows listing registered evaluators.

#### `voco evaluators:hosts`

Allows listing and testing connection to evaluation hosts.

Evaluation hosts can be configured in settings, see [configuration section](4_configuration.md) for more details.

Evaluation host need to be visible via the ping interface (configure it in `/etc/hosts`), and need to have a 
passwordless ssh connection configured using ssh keys.

> Docker setup and setup where evaluation hosts is local do not need to configure ssh/hosts

#### `voco evaluators:discover <hostname>`

Allows to connect to a host and register installed evaluation scripts.

BIN directory needs to be mapped in settings.

The bin needs to contain a `index.yml` file mapping the scripts to executors & base arguments.

Example : 

```yaml
evaluators:
  test:
    executor: bash
    script_path: /app-data/evaluators/test_eval.sh
    executor_arguments:
      - "-x" # run verbose mode

  test2:
    executor: python
    script_path: /app-data/evaluators/test_eval.py
    executor_arguments:
      - "-OO" # run with optimizations

```

#### `voco evaluators:args <ID> --arg1 <value> --arg2 <value> --flag-yes`

Allow altering base arguments to evaluator. 

## `voco leaderboards`

Allows to list/manipulate leaderboard data.
Root command allows listing registered leaderboards

#### `voco leaderboards:create`

Allows creating leaderboards.

> Fields: Label, Challenge ID, Entry Name, External Entry Location, Static Files
> Entry Name: the name of the leaderboard entry file in the submissions results (ex: entry.json)
> External Entry Location : path to load external entries (depracated)
> Static Files : feature to be implemented

An `-f <file.json>` option allows importing multiple leaderboards at the same time.

#### `voco leaderboards:edit <ID> <field> <value>`

Allows editing leaderboard fields Examples : 

* `voco leaderboards:edit <ID> entry_file item.json`
* `voco leaderboards:edit <ID> sorting_key date`

> Uses the date field to build the entry index

* `voco leaderboards:edit <ID> challenge_id 3`

#### `voco leaderboards:build <ID>`

Allows to run the leaderboard building process extracts all entries from relevant submissions and compiles them into a single `<leaderboard_label>.json` file.

#### `voco leaderboards:show <ID>`

Allows to print the result leaderboard.json file.
Root 

## `voco submissions`

Allows to manipulate user submissions.
Root command allows listing submissions

- `-u <UID>`: allows filtering by user
- `-t <ID>`: allows filtering by challenge
- `-s <status>`: allows filtering by status


#### `voco submissions:create <CHALLENGE_ID> <USER_ID> <ARCHIVE_FILE>`

Allows creation of a new submission by the administrator (does not auto eval). 

#### `voco submissions:eval <ID>`

Runs evaluation of a submission (syncs results if eval worker is remote)

#### `voco submissions:status <ID> <status>`

Allows manually setting the status of a submission.

Here is a list of all the available status : 

- uploading: submission is being uploaded
- uploaded: submission has finished uploading but has not been registered
- on_queue: submission is on queue waiting for eval/validation
- validating: submission is being validated
- invalid: submission has been found not valid
- evaluating: submission is beeing evaluated
- completed: submission has successfully been evaluated
- canceled: submission evaluation/validation has been canceled
- failed: submission evaluation has failed
- no_eval: submission does not have a registered evaluator
- no_auto_eval: submission is marked as not auto evaluated, needs admin to run eval
- excluded: submission is marked as excluded (from leaderboards)


#### `voco submissions:author_label <ID> <label>`

Allows manually setting a label for the submission.
> Feature usefull for leaderboard customisation

#### `voco submissions:upload <host> <ID>`


Allows syncing of submission with remote host.

> Should be only usefull in cases where automatic pipeline failed or custom evaluations. 
> Use eval instead, you should almost never need to do this manually

#### `voco submissions:fetch <host> <ID>`

Sync submission files from remote.

> Should be only usefull in cases where automatic pipeline failed or custom evaluations. 
> Use eval instead, you should almost never need to do this manually

#### `voco submissions:delete <CMD> <selector>`

Deletes a submission

List of CMD options :

- `by_id`: delete a submission using its ID
- `by_user` delete all submissions of a specific user
- `by_track` delete all submissions linked to a challenge

#### `voco submissions:evaluator <ID> <EVAL_ID>`

Set a specific evaluator to be used for this submission.

> By default when a submission is create the challenge evaluator is used.

#### `voco submissions:archive <CMD> <selector>`

Allows archival of a submission

> TODO: make archival more dynamic 

List of CMD options :

- `by_id`: archive a submission using its ID
- `by_user` archive all submissions of a specific user
- `by_track` archive all submissions linked to a challenge

## `voco worker`

Manipulate background workers

Root command allows inspection of the current queues.

#### `voco worker:generate:settings [-o OUTPUTFILE] {eval,update}`

Generate settings for a worker depending on its type.


#### `voco worker:generate:systemD [-o OUTPUTFILE] <settings-path>`

Generete systemD configuration for a worker based on the settings.


## `voco messaging`

Allows manually posting messages to a specific queue.

- `voco messaging:echo <message>`: Post a message to the echo-queue

> Queue used only for debuggin and testing messaging

- `voco messaging:update <SUBMISSION_ID> <status>`: Post a status update on the update-queue

> This triggers submission status update and rebuilding of leaderboards if relevant.

## `voco settings`

Allows printing current registered settings


#### `voco settings:template`

Prints a minimal .env file to run the platform.



