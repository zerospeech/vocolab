
# Zerospeech API

The Zerospeech API is created using [FastAPI](https://fastapi.tiangolo.com) micro-framework.


## Documentation

A thorough documentation of the API endpoints can be found at [<api_url>/docs]().


The documentation is automaticly generated from the code and contains variable types
and testing. The documentation interface is created using [OpenAPI](https://www.openapis.org) 
standard and [Swagger UI](https://swagger.io/tools/swagger-ui/). 

  
## Run 

The API is run using [Uvicorn](https://www.uvicorn.org) ASGI server.

You can find out more about [ASGI](https://asgi.readthedocs.io/en/latest/).

A Helper command exists to run the API locally

```bash
    $ zr-api
```

This command allows passing parameters to uvicorn. 

When used without any parameter it runs the api with the following scheme 

```bash
    $ uvicorn zerospeech.api:app --reload --debug
```


> The zerospeech module needs to be installed (see README for details).
## Deployment

To use the API in production we need the following components


1. [Uvicorn](https://www.uvicorn.org): the wrapper around the ASGI protocol.

2. [Gunicorn](https://gunicorn.org): WSGI server.

3. [NGINX](https://www.nginx.com): As a reverse proxy to the external network.


The ASGI protocol is an extension of the WSGI to include asynchronous tasks,
for this reason we configure Gunicorn use Uvicorn as a worker. 

There are some advantages to Using Uvicorn as a worker for Gunicorn instead of using 
it directly as our server as we do in devellopement mode :


1. Gunicorn is a more mature, fully featured server and process manager.

2. Increase or decrease the number of worker processes.

3. Restart worker processes gracefully, or perform server upgrades without downtime.



We can deploy Gunicorn with the following command using 4 worker processes : 

```bash 
$ gunicorn zerospeech.api:app -w 4 -k uvicorn.workers.UvicornWorker
```


The usage of NGINX (or equivalent) as a reverse proxy allows having a robust solution
in charge of network level manipulations (https certificates, domain name, load balancing, caching, etc).
## Config Files

### API
To Config the Api we use a .env file 

  
### Gunicorn


```INI
[zerospeech.api:app]
use = egg:gunicorn#main
host = 192.168.0.1
port = 80
workers = 2
proc_name = brim
```

#### SystemD


```INI
[Unit]
Description=Zerospeech API
After=syslog.target
After=network.target

[Service]
Type=simple
User=zerospeech
Group=zerospeech

# Start container when unit is started
ExecStart=/location/gunicorn ....

# Give a reasonable amount of time for the server to start up/shut down
TimeoutSec=300

[Install]
WantedBy=multi-user.target

```


### NGINX


```
  server {
    listen 80;
    server_name api.zerospeech.com;
    access_log  /var/log/nginx/zerospeech.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
  }
```