# VocoLab ![BETA](https://img.shields.io/badge/-BETA-blue)

A module allowing administration of challenges.

![VERSION](https://img.shields.io/badge/VocoLab-V0.5--beta-orange) ![LICENCE](https://img.shields.io/badge/LICENCE-GPL%20%3E=%20V3-green)![BUILD](https://img.shields.io/badge/BUILD-OK-green)![TESTS](https://img.shields.io/badge/TESTS-Not%20Setup-red)

VocoLab is a module that allows administration of various challenges, it includes :

1) user management (login/logout, signup, password reset)
2) multiple challenge creation (or multiple task depending on setup)
4) Submission upload & management
3) Automatic evaluation of submissions (using a message queue & an asychronous evaluation worker)
4) Configurable evaluations that can run in a remote server via multiple type of runners (bash, python, slurm, etc)
4) Aggregation of results into a leaderboard.
5) Access to all the information using an API.


Some feature details :

- A submission can be of anything that can be included in a zip archive.
- A large submission can benefit of multipart upload (file spliting).
- Each challenge (or task) can have only one evaluation script.
- Evaluation can be triggered on demand by admin or automaticly.
- Administrator can setup evaluation quotas (number of submissions per hour/day/month etc...)
- Each challenge (or task) can have multiple leaderboards.
- A leaderboard can contain any type of value in any format each entry consists of a json object.
- When an evaluation is completed all the relevant leaderboard are rebuilt.
- Evaluators can be any type of script (python/bash/etc..)


## Setup

Setup can be handled in three ways the first is using docker which is the easier, the second is to perform a
native installation of all the tools & components necessairy. The third is local mode which is used during devellopement to debug and test the different features.

### Simple Setup w/ Docker

Using docker, you can use the default configurations and create all the services without having to install and setup all dependencies. 

This creates all the necessary services to run VocoLab. To use the docker version, you need to install docker & docker-compose on your server ([installation instructions](<https://docs.docker.com/compose/install/>)). 
Once docker is up and running you can setup vocolab : 


0) Clone this repository `git clone <url> <folder>` somewhere on your server.
1) Edit the default environment default settings in the [docker-compose.yml](docker-compose.yml) file, and replace them with your own (API_BASE_URL, SMTP settings, etc..), there is a detailed description of all possible env variables [here](docs/settings.md).
2) Start the services `docker-compose up -d` (the `-d` allows docker to be run un daemon mode).
3) A reverse proxy will need to be setup to allow access to the API from the outside world. (see how to setup a reverse proxy in the [setup section](...))
4) Now all you need to do is add some challenges/users/leaderboards and you are good to go. You can find a quick-setup example with our own data [here](...)

> The evaluation worker node will probably need to be local or on another machine if you require more computing power for
> evaluation. You can see how to set-up remote workers in the [setup section](...)


### Manual Setup

A manual setup requires a bit more work to setup as you will have to manage and install all the dependencies.

##### Dependencies

To run this project, you will need to add the following environment :

1. python 3.7+
2. An instance of [RabbitMQ](https://www.rabbitmq.com) installed.
3. A daemon manager ([SystemD](), [SupervisorD](http://supervisord.org), etc...) 
4. A reverse proxy ([Nginx](https://www.nginx.com/resources/wiki/), [Apache](https://httpd.apache.org/docs/), etc..)

A detailed explanation on how to install & setup all the services manually can be found [here](...)

##### Environment Configuration

To configure your environment a .env file is used. you need to specify an 
environment variable named `VC_ENV_FILE` configured, so the module knows were 
load variables from.

For an example on the minimum setup see [example.env](samples/example.env)

More information on settings and the meaning of each parameter can be found [here](docs/settings.md)

> If some variables are not set correctly it might affect some features of the module as they are a hard dependency.

### Local Devellopment Setup

Install the following dependencies: 

1. python 3.7+
2. An instance of [RabbitMQ](https://www.rabbitmq.com) installed.


Clone the project

```bash
  git clone <url> <vocoLab>

```

Go to the project directory

```bash
  cd vocoLab

```

Create an environment and install dependencies

```bash
  python -m virtualenv venv
  source venv/bin/activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt

```

Install the package locally

```bash
  pip install -e .

```

Now you can run the following commands :

```bash
 voco api:init
```

* `voco` : CLI with all the admin tools.
* `voco api:serve` : run the api in debug mode locally.
* `voco worker:run -t eval` : run the evaluation worker.
* `voco worker:run -t update`: run the update worker.

## Documentation ![WIP](https://img.shields.io/badge/-WORK%20IN%20PROGRESS-orange)

More detailed documentation of each component and how it works can be found
in the [docs](docs/) folder.

The [samples folder](samples/) contains some examples of challenges/users & leaderboards to allow illustration of 
how the tool works.

> The samples folder is a ![WIP](https://img.shields.io/badge/-WORK%20IN%20PROGRESS-orange)

1. [Installation & Setup](docs/1_setup.md)
2. [Quick Start](docs/2_quickstart.md)
3. [Administration](docs/3_administration.md)
4. [Configurations](docs/4_configuration.md)
5. [Examples](docs/5_examples.md)
6. [Evaluations](docs/6_evaluations.md)

## Testing ![WIP](https://img.shields.io/badge/-TODO-red)

To run tests execute the following command : `pytest`

For more information on tests see [docs/testing](docs/testing.md)


## License

vocolab module 

Copyright (C) 2021 Nicolas Hamilakis, CoML TEAM, École Normale Supérieure Paris, Inria Paris Research
This program and all its files are licenced under the GNU GENERAL PUBLIC LICENSE Version 3;
This program comes with ABSOLUTELY NO WARRANTY;
This is free software, and you are welcome to redistribute it under certain conditions;
For more information on the Terms & Conditions see the details in the [LICENCE.txt](LICENCE.txt) file attached to this project,
or consult the online version of the [GPL v3](https://choosealicense.com/licenses/gpl-3.0/)


