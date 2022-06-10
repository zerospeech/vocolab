# How to Create a new challenge

1) create the database entry for the challenge
   run the command `zr challenges:add`

2) write an evaluator script upload it to one of the configured hosts.

3) specify the output files of the evaluator.

    - leaderboard entries (ex: `track1-entry.json`) should go into the root of each submission dir
    - if any static files are produced they need to go under 'static' directory
      in the root of the submission
      
4) Run the evaluator discovery tool `zr evaluators:discover <hostname>` this should add
   all the new evaluators into the database.
   
5) create a leaderboard `zr leaderboards:create`

6) bind the challenge with the evaluator `zr challenges:set evaluator <id>`

7) setup external entries for leaderboard or include static files if needed.

> zr leaderboards:edit <id> external_entries /path/to/entries

> zr leaderboards:edit <id> static_files true

**Static files are fetched from a `static` subdir in external entries folder or in each
of the submission's folder.

8) activate the challenge `zr challenge:set <id> active true`
   this allows submissions to be added by the users.
   
9) you can manually build the leaderboard by running `zr leaderboard:build <id>`

**If no submissions are found the leaderboard is build with the external entries only.

**An archived leaderboard builds only from external entries.


## Useful commands

All available commands can be found by running `zr help`

- Listing available challenges: `zr challenges -a` (-a shows all challenges (active/inactive, completed)

- Listing available leaderboards `zr leaderboards`

- Listing available evaluators `zr evaluators`

- Listing available hosts `zr evaluators:hosts` (also checks availability)

**All hosts should be configured to have passwordless ssh connection via key files.


# Configuring evaluators

All remote hosts need to be configured with 3 variables:

- settings.HOSTS: a list of all hostnames

- settings.REMOTE_STORAGE: a dictionary binding each hostname to a path to a storage folder tp upload submissions

- settings.REMOTE_BIN: a dictionary binding each hostname to a directory containing evaluator scripts.

** Evaluator scripts are discovered by the api using an index.yaml file.

Example: 

```yaml
evaluators:
  test:
    executor: bash
    script_path: /zerospeech/bin/test.sh

  zr2020-eval:
    executor: bash
    script_path: /zerospeech/bin/zr2020-eval.sh
  
  zr2021-eval:
    executor: bash
    script_path: /zerospeech/bin/zr2021-eval.sh
```