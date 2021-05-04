
# Zerospeech CLI Admin tool

A command line tool to visualise & administrate data used by the Zerospeech API 


## Usage

```bash
❯ zr --help
usage: zr <command> [<args>]

Zerospeech Back-end administration tool

positional arguments:
  command     Subcommand to run

optional arguments:
  -h, --help  show this help message and exit

list of available commands : 

users:

users:list	lists available users
users:logged	list logged users
users:create	create a new user

challenges:

challenges:list	 Command to list all challenges
challenges:new	 Command to create new challenges 
challenges:set	 Command to alter properties of Challenges

check:

check:settings	check current instance settings value

submissions:

submissions:list	 List submissions 
submissions:set	 Set submission status 
submissions:evaluate	 Launches the evaluation of a submission 
submissions:create	 Adds a submission 

evaluator:

evaluator:hosts	 Command to list all hosts containing evaluators 
evaluator:list	 Command to list all registered evaluators
evaluator:discover	 Command to list all challenges


```

  
## Documentation


### Users

Commands that maniputate users


+ `users:list`: lists all users in the database.

+ `users:logged`: lists all users currently logged in the API.

Options:
```bash
  --close CLOSE  user to close sessions of a specific user
  --close-all    close all open sessions
```

+ `users:create`: allowes direct creation of a user

Options:
```bash
  -f FROM_FILE, --from-file FROM_FILE
                        Load users from a json file
```


### Challenges

Commands that maniputate Challenges

+ `challenges:list`: list all active challenges in the database.

Options:
```bash
  -a, --include-all  include non-active/expired challenges
```

+ `challenges:new`: create a new challenge.

Options:
```bash
  --dry-run             does not insert into database
  -f FROM_FILE, --from-file FROM_FILE
                        Load challenges from a json file
```

+ `challenges:set`: Alter the property of a challenge.

Options:
```bash
usage: challenges:set [-h] id field value

positional arguments:
  id          ID of the challenge to update
  field       the field that will be updated
  value       the value to add
```

> date fields accept strings in the format: dd/mm/yyyy 


### Check

Allows to verify if all components work correctly.

+ `check:settings`: check current settings variables.

Options:
```bash
  --get GET   Retrieves a specific value
  --info      Info on how to set settings
  --keys      List all available keys
```

### Submissions

Allows manipulation of submissions in the api.


+ `submissions:list`: Lists all submissions made by the users.

Options:
```bash
  -u USER, --user USER  Filter by user ID
  -t TRACK, --track TRACK
                        Filter by track ID
  -s STATUS--status STATUS
                        Filter by status

status values: {uploading,uploaded,on_queue,validating,invalid,evaluating,completed,canceled,failed}
```

+ `submissions:set`: Allows updating a submissions status.

+ `submissions:evaluate`: Launches the evaluation (re-evaluation) of a submission.

+ `submissions:create`: Adds a new submission (by passes the API) 

    > [to be used for debbuging and special cases]


### Evaluators

Allows administration of evaluators.

> Evaluators are procedures (scripts) that allow evaluation of submissions.
> These scripts are called using the message queue and a worker will be reponsible for 
> running them. 

+ `evaluator:hosts`: Lists all registered hosts containing evaluators.

    > To add/remove hosts see [docs/settings](settings.md)

+ `evaluator:list`: Lists registered evaluators in database.

+ `evaluator:discover`: Run the discover script that registers evaluators.

    > A passwordless ssh connection with ssh key files must be setup in advance.

    > A index.yml file must be created in the root of the directory containing evaluators.

    For more information see [workers](workers.md)


