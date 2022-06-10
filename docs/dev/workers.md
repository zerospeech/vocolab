# Background Workers

Background workers allow you to run long-running tasks that require more time.
In this module we have 3 types of background workers

## Eval Worker

Evaluation worker handles the evaluation of submissions. 

It listens on the queue for incoming evaluation messages send from 
the api (or the admin through the cli).

#### Run evaluation worker

```bash
❯ zr worker:run:eval -h
usage: zr worker:run:eval [-h] [-w NB_WORKERS] [--prefetch-count PREFETCH_COUNT]

 Run evaluation task worker 

optional arguments:
  -h, --help            show this help message and exit
  -w NB_WORKERS, --number-of-workers NB_WORKERS
                        Number of processes to allow for workers
  --prefetch-count PREFETCH_COUNT
                        Number of simultaneous messages allowed to be pulled by one process
```

#### Evaluation Protocol

The api (or the cli) transfers the submission data to the worker host 
(must have a passwordless ssh connection setup), and then sends an evaluation request
through rabbit-mq. 

Once the worker receives an eval message it process the arguments and finds the correct
evaluation script (in the configured bin folder) to run on the eval files.

Once completed the worker sends a message through the update queue to notify of the
completion of the evaluation.


## Update Worker

The update worker runs along-side the api and handles update events.

Event types:

1. evaluation-complete:
    - marks the evaluation as complete on the database
    - transfers result files from eval host
    - rebuilds dependant leaderboards
2. evaluation-failed:
    - marks evaluation as failed on the database
    - transfers logs from eval host
3. evaluation-canceled:
    - marks evaluation as canceled on the database
    - transfers logs from eval host
   
#### Run update worker

```bash
❯ zr worker:run:update -h
usage: zr worker:run:update [-h] [-w NB_WORKERS] [--prefetch-count PREFETCH_COUNT]

 Run update task worker 

optional arguments:
  -h, --help            show this help message and exit
  -w NB_WORKERS, --number-of-workers NB_WORKERS
                        Number of processes to allow for workers
  --prefetch-count PREFETCH_COUNT
                        Number of simultaneous messages allowed to be pulled by one process
```

## Echo Worker

A worker that only receives log messages, used mainly for debugging queue processes. 