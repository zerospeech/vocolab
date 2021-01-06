# API


- [ ] Settings
    
    - [X] Global settings with subsections
    - [X] Cache settings for faster creation/parsing
    - [X] Load settings local env from file/env_file 
    
- [X] Logging

- [ ] index route should be a page, with links to docs & website

- [ ] ....
 
## Auth 

- [X] user login

    - [X] create user_db (users & logged users table)
    - [X] add a security layer on passwords (hash & salt passwords, session expiry, etc)
    - [X] add logout (delete session) & clean-up function for expired sessions
    - [X] add routes for login/logout/check using OAuth2PasswordBearer schema
    - [X] create generic function to get & validate session to be used as dependencies for all log protected routes
    - [X] mount /auth sub-route to api
    - [ ] create pytest cases for all auth functions

- [X] user registration
    
    - [X] add a function that handles insertion of new user
    - [X] add function to send email to new user for verification
    - [X] add route for user creation
    - [X] inherit login security features
    - [X] send email on registration to verify email
    - [X] create route for email validation page (with template)
    - [ ] add a delete user function (that deactivates the account) !!! should have triple confirmation
    - [ ] create pytest cases for all registration functions

- [X] reset password

    - [X] create reset password session table
    - [X] create safe/unsafe password reset routes
    - [X] send email for password reset session to user
    - [X] create route for password reset page (with html template)
    - [ ] add pytest cases for all registration functions

## User 

- [X] add user profile section

- [X] add user profile back-end data (probably as json files ?)


## Notify

- [X] Mattermost Notification
    
    - [X] Use jinja2 templates for messages
    
    - [X] create bot hook for messaging

- [X] Email Notification

    - [X] Load email configs from env
    
    - [X] use jinja2 templates for emails
 

## Challenges 


- [ ] create database for all challenges
        
features:

    - mark as active
    - url
    - list of evaluators
    - leaderboard
    - ressources index (download data)
    - submissions list
    - participants list
    

# Evaluation Pipeline

- TaskQueue on oberon

- Namespace zerospeech for custom functions per challenge

- Feedback on progress of pipelines via api


# Scheduler

- Basic scheduling using cron (cleanups, notification, etc)


# Admin CLI

An Extensive CLI that allows local manipulation of all the data of the API directly on the server

- Job scheduling (via cron wrapper)

- Evaluation monitoring

- Notification activation

- Data Manipulation (users, challenges, etc)

- Handle to add, remove, deactivate challenges 