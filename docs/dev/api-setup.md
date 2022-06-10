# How to set up the api

## Preparation

1) clone this repository into a folder.

2) create a python3.7+ virtual-environment : `python3 -m virtualenv myenv`

3) activate your environment : `source path/to/myenv/bin/activate`

4) install the module by running `pip install .` inside the cloned folder.

5) if the installation was correct the command `zr help` should print various information.

6) generate a configuration file : `zr settings:template > my_settings.env`

**This is an example file you will need to manually set most of the values to correspond 
to your runtime. The template has a minimal set of variables needed to run the api.
A more exhaustive list can be found by running `zr settings --keys`

For more info on how the settings work run `zr settings --info`

7) DATA_FOLDER: a data folder is required to store all the permanent data (sqlite database, submissions, leaderboards, etc).
   to create the basic architecture you can use the following script `bash scripts prestart.sh <location>`.


8) Once the .env file is complete an environmental variable is required to tell the
   api where to find it : `> export ZR_ENV_FILE=/path/to/my_settings.env`
   you can check if settings are loaded correctly by running `zr settings`
   

9) A debug version of the API can be run by executing : `zr api:debug`
   
## Production installation

> This is installation is based on a nginx proxy, with gunicorn server managed by systemd
> other setups can work as well but tutorials are not included.

1) setup gunicorn server file : `zr api:config:gunicorn -o server.py`

** For more info visit : [gunicorn documentation](https://docs.gunicorn.org/en/latest/settings.html#config-file)

2) setup systemd socket unit :

```bash
> zr api:config:socket -o gunicorn.socket
> sudo cp gunicorn.socket /etc/systemd/system/
```

3) setup systemd service unit file : 

```bash
> zr api:config:service -o gunicorn.service server.py
> sudo cp gunicorn.service /etc/systemd/system/
> sudo systemctl daemon-reload
> sudo systemctl enable --now gunicorn.socket
> sudo systemctl enable --now gunicorn.service
```

** If any files or path are modified you need to manually edit .service & server.py
to correspond to those changes.

4) setup nginx proxy : 

```bash
> zr api:config:nginx -o api.conf
> sudo cp api.conf /etc/nginx/sites-available/
> sudo ln -s /etc/nginx/sites-available/api.conf /etc/nginx/sites-enabled/api.conf
> sudo systemctl reload nginx.service # or other command allowing to reload nginx
```

**! extra steps must be added to auto-generate certificates for secure https connection.
see [this article](https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/)


> All values set in the templates are configurable via settings. 


# Updating the API

To update the version of the running API :

1) `git pull` (in the module folder a newer version)

2) `source myenv/bin/activate` activate the environment

3) `pip install .` install the updated version in the current environment

4) `sudo systemctl reload gunicorn.service` reload the service.
