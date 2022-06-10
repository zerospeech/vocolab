# VocoLab ![SETUP](https://img.shields.io/badge/-SETUP-blue)

The VocoLab library is comprised of two components, the API and workers. 
In a basic setup you would have 1 service for the API, 1 for the evaluation worker (worker responsible for handling the evaluation of submissions)
and 1 worker to manage various updates and other background jobs for the API.

## Docker ![SETUP](https://img.shields.io/badge/-SETUP-blue)

Using docker, you can use the default configurations and create all the services without having to install and setup all dependencies. 

This creates all the necessary services to run VocoLab. To use the docker version, you need to install docker & docker-compose on your server ([installation instructions](https://docs.docker.com/compose/install/)). 
Once docker is up and running, you can set up vocolab : 

1. Clone this repository `git clone <url> <folder>` somewhere on your server.
2. Edit the default environment default settings in the [docker-compose.yml](../docker-compose.yml) file, and replace them with your own (API_BASE_URL, SMTP settings, etc…), there is a detailed description of all possible env variables [here](4_configuration.md).
3. Start the services `docker-compose up -d` (the `-d` allows docker to be run un daemon mode).
4. A reverse proxy will need to be setup to allow access to the API from the outside world. (see how to set up a reverse proxy [below](#reverse-proxy))
5. Now all you need to do is add some challenges/users/leaderboards, and you are good to go. You can find a quick-setup example with our own data [here](...)

> The evaluation worker node will probably need to be local or on another machine if you require more computing power for
> evaluation. You can see how to set-up remote workers in the [worker-setup](...) section

## Manual ![SETUP](https://img.shields.io/badge/-SETUP-blue)

The manual installation requires you to set up some dependencies before beginning: 

1. python 3.7+
2. An instance of [RabbitMQ](https://www.rabbitmq.com) installed.
3. A daemon manager ([SystemD](<>), [SupervisorD](http://supervisord.org), etc…) 
4. A reverse proxy ([Nginx](https://www.nginx.com/resources/wiki/), [Apache](https://httpd.apache.org/docs/), etc…)

### API

1. To install the API, you need to clone this repository

```bash
  git clone <url> <vocoLab>

```

1. Go to the project directory

```bash
  cd vocoLab

```

1. Create an environment and install dependencies

```bash
  python3 -m virtualenv venv
  source venv/bin/activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt

```

1. Install the VocoLab package

```bash
  pip install .

```

1. Configure your environment.

Create a .env file containing your configurations, here is a minimal example : 

```sh
# ROOT API URL
VC_API_BASE_URL="https://api.example.com"
VC_DATA_FOLDER=/location/to/app-data/
# SMTP SETTINGS
VC_MAIL_USERNAME=noreply@vocolab.com
VC_MAIL_PASSWORD=XXXXXXX
VC_MAIL_FROM=noreply@vocolab.com
VC_MAIL_FROM_NAME="Vocolab Challenges"
VC_MAIL_PORT=25
VC_MAIL_SERVER=mail.vocolab.com
VC_MAIL_TLS=True
VC_MAIL_SSL=False
# USER & Group settings
VC_SERVICE_USER=vocolab
VC_SERVICE_GROUP=vocolab

```

> a more exhaustive list of settings can be found [here](4_configuration.md)

Once this file is created, you need to set an environment variable pointing to it 

```bash
 export VOCO_ENV_FILE="/path/to/my.env"

```

> Alternativly all configurations can be also overloaded by env variables prepended by `VC_`.

to check if your setting are loaded correctly run `voco settings`

1. Once our settings are set up, we can test the installation.

Initialize the env

```sh
	voco api:init
    voco api:debug

```

You should be able to see the API by navigating on your browser to <http://127.0.0.1:8000/docs>

If the page loads with the API documentation page, you successfully set up the API.

##### Setup API Daemon

For the API to run permanently in the background, you need two things, an AWSGI handler and a daemon manager.
\- For AWSGI we recommend [Gunicorn](https://gunicorn.org).
\- For the daemon manager, we will use [SystemD](https://www.freedesktop.org/wiki/Software/systemd/)

> You are free to use alternatives to those but configurations and setup will differ.

1. Create an etc folder to store your configurations `mkdir /location/etc/vocolab`
2. Generate Gunicorn server file

```bash
	voco api:config:gunicorn -o /server/etc/vocolab/server.py

```

> You can check-out gunicorn documentation and edit configurations depending on your preferences.

1. Generate SystemD unit & socket file

```bash
 voco api:config:service -o /location/etc/vocolab/voco-api.service /server/etc/vocolab/server.py
 voco api:config:service -o /location/etc/vocolab/voco-api.socket 

```

> Various customisations can be made, checkout systemD documentation

1. Copy unit files to systemD location (may vary depending on system)

```bash
 sudo cp /location/etc/vocolab/voco-api.service /etc/systemd/system/
 sudo cp /location/etc/vocolab/voco-api.socket /etc/systemd/system/
 sudo systemctl daemon-reload # reload systemd daemon list

```

1. Enable Services

```bash
 sudo systemctl enable voco-api.service
 sudo systemctl enable voco-api.socket
 sudo systemctl start voco-api.service

```

Now the service should run permanently in the background. 

> To make it available to the outside world see [Reverse Proxy Section](#reverse-proxy)

### Update Worker

The update Worker needs to be installed next (the same env) to the API service as in needs access to the database.
The update worker will handle events triggered by the api/eval workers, that require background time. (leaderboard update, file sync, etc). 

1. Before setting up the update worker, we need to set up RabbitMQ settings. We need to append the following values to our `my.env`file:

```sh
# RabbitMQ Setup
# -- add connection info for RabbitMQ
VC_RPC_USERNAME=vocolab
VC_RPC_PASSWORD=admin123
VC_RPC_HOST=vocolab_queue
VC_RPC_PORT=5672

```

> these values will depend on the configuration you did on RabbitMQ

1. Generate Daemon file & settings

```sh
 voco worker:generate:settings -o /location/etc/vocolab/voco-update.settings update
 voco worker:generate:systemD -o /location/etc/vocolab/voco-update.service /location/etc/vocolab/voco-update.settings

```

1. Copy unit file & enable it

```sh
 sudo cp /location/etc/vocolab/voco-update.service /etc/systemd/system/
 sudo systemctl daemon-reload
 sudo systemctl enable voco-update.service

```

1. Start the update worker

```sh
 sudo systemctl start voco-update.service

```

> You should also reload the api to recognise new settings `sudo systemctl reload voco-api.service`

### Evaluation Worker

The evaluation worker will handle the evaluations of the submissions, depending on your setup you might want 
to install this worker on a different server that the API (if you require more computing power, for example).

1. Setup Path for API/Update

On the server where the API/Update services are running, edit the `my.env` file with the following values, depending on the case : 

* evaluation worker on same machine as API

```sh
VC_HOSTS='["localhost"]'
VC_REMOTE_BIN='{"localhost":"/location/evaluators/bin"}'

```

* evaluation worker on different machine as API

```sh
VC_HOSTS='["remoteHost"]'
VC_REMOTE_STORAGE='{"remoteHost":"/vocolab/submissions"}'
VC_REMOTE_BIN='{"remoteHost":"/location/evaluators/bin"}'

```

> the remoteHost needs to be the hostname/IP of the machine where the worker is installed.
> SSH passwordless connection needs to be configures to this machine using ssh keys
> The hostname should resolve using the ping protocol (add it to /etc/hosts).

Reload api & update services `sudo systemctl reload voco-api.service` & `sudo systemctl restart voco-update.service`

1. If you are installing on a different machine you will need to reinstall the package & create a .env file same as you did for the API installation, if not skip this step, and use the same environment as other services.
2. Generate Daemon file & settings

```sh
 voco worker:generate:settings -o /location/etc/vocolab/voco-eval.settings eval
 voco worker:generate:systemD -o /location/etc/vocolab/voco-update.service /location/etc/vocolab/voco-eval.settings

```

1. Copy unit file & enable it

```sh
 sudo cp /location/etc/vocolab/voco-eval.service /etc/systemd/system/
 sudo systemctl daemon-reload
 sudo systemctl enable voco-eval.service

```

1. Start the update worker

```sh
 sudo systemctl start voco-eval.service

```

You have successfully set up the evaluation worker. Next, you need to add some evaluators (see quick-start section).

### Reverse Proxy

Gunicorn is an WSGI/AWSGI daemon manager, but should not be used as an HTTP server instead a better setup is 
to add a reverse proxy on a more stable and complete server, we suggest using Nginx (but Apache or others can be used instead, although setup will be different).

Once nginx is set up and installed, generate the conf file using the CLI & add it to nginx

```sh
 voco zr api:config:nginx -o /location/etc/vocolab/www-vocolab.conf
 # add it to available sites
 sudo cp /location/etc/vocolab/www-vocolab.conf /etc/nginx/sites-available/ 
 # enable the site
 sudo ln -s /etc/nginx/sites-available/www-vocolab.conf /etc/nginx/sites-enabled/www-vocolab.conf

```

Check if nginx configuration is correct and reload nginx

```sh
 sudo nginx -t
 sudo systemctl restart nginx

```

Once this is done, your API should be available on your domain via the URL: <http://api.example.com>

> You need to configure your DNS to point to your server ofc

It is recommended to add an SSL certificate to secure your API, you can use [letsencypt](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-20-04) for free or any other certificate service you want.


