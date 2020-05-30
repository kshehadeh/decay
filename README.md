# decay
This tool will validate that a given folder within a git repository contains documents that have been updated within a set period of time. The intention is to help keep documentation as fresh as possible.  After `STALE_AGE_IN_DAYS` days have passed since the last commit, the document is said to beging decaying.    

## Usage
This script is meant to be used as part of a CI process such as Github Actions or Circle CI.  You can specify the configuration either in a yaml file, in the environment or on the command-line.    

Example configuration:

```yaml
# ~/decay.yml
actions: [email_owner,send_admin_report]
github_owner: "underarmour"
github_repo: "infra"
github_repo_folder: "/"
github_access_token: "<token>"
email_owner: "true"
administrator: "myemail@domain.com"
admin_report: "true"
github_branch: "master"
from_email: "noreply@domain.com"
sendgrid_api_key: "<key>"
ignore_path: ["/announcements","/_posts", "/legacy","posts/templates/"]
ignore_file: ["index.md"]
```
```bash
~> decay 
```

With the configuration file in the current working directory, all config values will be picked up from there and used.  You can
also specify a configuration location of your choice.

```bash
~> decay -c ~/myconfigfile.yml
```

And of course you can use command line arguments for all configuration:

```bash
~> decay --github_owner="underarmour" \ 
         --github_repo="infra" \
         --github_repo_folder="/" \
         --github_access_token="<token>" \
         --email_owner="true" \
         --administrator="myemail@domain.com" \
         --admin_report="true" \
         --github_branch="master" \
         --from_email="noreply@domain.com" \
         --sendgrid_api_key="<key>" \
         --ignore_path=["/announcements","/_posts", "/legacy","posts/templates/"] \
         --ignore_file=["index.md"] 
```

## Actions

Decay can perform multiple actions either in one command run or separately as part of a series of commands. The actions to perform are:

### `email_owner`
Sends a single message containing a list of all the documents that are fall outside of the "fresh" range of dates specified in the configuration.  For example, if you have set `STALE_AGE_IN_DAYS` to 30 and a doc has not been updated in 31 then an email will be sent to the owner of that file.  If no owner has been specified then the administrator will be notified. If no admin has been passed into the command then an error message will be shown during command run.

### `send_admin_report`
Send a single email to the administrator with a list of all the documents being reviewed along with the age and the last editor of each.  This is meant to be used to provide a full state of documentation for a given repo (or sub-repo).

### `mark`
Rather than sending an email to owners or administrators, this will update the document itself with the new state.  For example, if the doc has not be updated in over `STALE_AGE_IN_DAYS` then `out_of_date` will be set to `true`.  

Each file updated is done as a separate commit - for that reason, it makes the changes in a separate branch then opens a PR against the source branch specified in the `github_branch` argument.  By default, this will be `master`.  

It is recommended that when merging the PR that you use the `Squash and Merge` option - especially if a lot of files have changed.

## File Types
While it is designed to help identify stale documentation, it can be used for any type of file within a given root. By default it looks for markdown and html files.  But you can change the file types using the `--extensions` argument.  

## Owners
If the files that are being checked have frontmatter sections at the top of the file, it will look for an `owner` field which, if it's an email, will be used to notify that owner of stale documentation if the `email_owner` property is set to `true`.  

Example of frontmatter with owner property:
```
---
layout: page
title: Access to Amazon Web Services
permalink: /:path/:basename:output_ext
parent: Amazon Web Services
summary: How to get access to AWS
nav_order: 1
owner: bob@email.com
---

# Access to AWS
...

```

## Administrator
There is also the notion of an administrator.  The administrator is the person that, if `email_owner` is set but an owner could not be found, will receive the notification emails.  If `send_admin_report` is true then the administrator will also receive a report of all the files that were checked, their age, which are now considered stale and who the last person to change the file was.

## Reports
There are two types of reports: owner and admin.  

The owner report is sent to anyone who is marked as an owner of at least one document that is beginning to decay.  For example, if there is a folder that looks like this:

```
+ docs
    - index.md (owner is bob@email.com, decaying)
    - info.md  (owner is bob@email.com)
    - access.md(owner is john@email.com, decaying)
```

In this case, two owner reports will be sent out.  The first will contain exactly one file (index.md) and be sent to bob@.  The other will contain only file and will be sent to john@.  Notice that info.md is not sent anywhere because it hasn't be tagged as decaying. 


  
## Arguments

Arguments can be provided either on the command line, in environment variables or in a YAML file called `decay.yml` in the current working directory.  You can also specify a config file to use with the `-c` or `--config` argument.  The order of preference for configuration variables is:

1. Command-line
2. Environment
3. Config File

```
usage: main.py [-h] [-c CONFIG] -o GITHUB_OWNER -g GITHUB_REPO -f
               GITHUB_REPO_FOLDER [-b GITHUB_BRANCH] -a GITHUB_ACCESS_TOKEN
               [-s STALE_AGE_IN_DAYS] [-e EMAIL_OWNER] [-k SENDGRID_API_KEY]
               [-r FROM_EMAIL] [-x EXTENSIONS] [-m ADMINISTRATOR]
               [-p ADMIN_REPORT]

Generate reports on documentation decay 

Args that start with '--' (eg. -o) can
also be set in a config file (./decay.yml or specified via -c). The config
file uses YAML syntax and must represent a YAML 'mapping' (for details, see
http://learn.getgrav.org/advanced/yaml). If an arg is specified in more than
one place, then commandline values override config file values which override
defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to YAML configuration file
  -o GITHUB_OWNER, --github_owner GITHUB_OWNER
                        The organization name is the owner
  -g GITHUB_REPO, --github_repo GITHUB_REPO
                        The repository name (excluding the path)
  -f GITHUB_REPO_FOLDER, --github_repo_folder GITHUB_REPO_FOLDER
                        The path of the file in the repo - starting without a
                        leading slash
  -b GITHUB_BRANCH, --github_branch GITHUB_BRANCH
                        The branch to use for the repo - uses 'master' by
                        default.
  -a GITHUB_ACCESS_TOKEN, --github_access_token GITHUB_ACCESS_TOKEN
                        The personal access token to use - keeping in mind
                        that the token needs to have access to any SSO-
                        protected repo
  -s STALE_AGE_IN_DAYS, --stale_age_in_days STALE_AGE_IN_DAYS
                        The number of days of no activity after which a file
                        is considered to be stale.
  -e EMAIL_OWNER, --email_owner EMAIL_OWNER
                        Set to 'true' if the script should email the owner of
                        stale files.
  -k SENDGRID_API_KEY, --sendgrid_api_key SENDGRID_API_KEY
                        This is the sendgrid api key to use when email_owner
                        is set to True. This value IS required if email_owner
                        is set to true.
  -r FROM_EMAIL, --from_email FROM_EMAIL
                        This is the email that sent emails will appear to come
                        from
  -x EXTENSIONS, --extensions EXTENSIONS
                        These are the file extensions that will be checked
                        within the given root
  -m ADMINISTRATOR, --administrator ADMINISTRATOR
                        The admin will receive the admin report (if arg set)
                        and any emails that would be sent to an owner - but
                        one does not exist.
  -p ADMIN_REPORT, --admin_report ADMIN_REPORT
                        These are the file extensions that will be checked
                        within the given root

```
