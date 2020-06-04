# decay
![Decay Logo](docs/tooth-64.png)
Decay is a documentation tool for analyzing existing documentation.  The goal of the tool is to help documentation maintainers track the age of the documentation and help to ensure that it remains up-to-date.   The tool can target documentation stored in Github and Confluence.

## Usage
The tool performs actions each with different purposes.  It can generate reports to send to doc owners, generate reports to send to 'administrators' of the documentation and it can update the docs themselves indicating whether they are out of date (assuming they use frontmatter).  See `actions` section below for more information about how to use each.  

In general, this tool is meant to be used as part of a CI process such as Github Actions or Circle CI.  You can specify the configuration either in a yaml file, in the environment or on the command-line or some combination of any of those three.    

Example configuration:

```yaml
# ~/decay.yml
actions: [email_owner,send_admin_report]
github_owner: "underarmour"
github_repo: "infra"
github_repo_folder: "/"
github_access_token: "<token>"
administrator: "myemail@domain.com"
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
~> decay email_owner send_admin_report \ 
        --github_owner="underarmour" \ 
         --github_repo="infra" \
         --github_repo_folder="/" \
         --github_access_token="<token>" \
         --administrator="myemail@domain.com" \
         --github_branch="master" \
         --from_email="noreply@domain.com" \
         --sendgrid_api_key="<key>" \
         --ignore_path=["/announcements","/_posts", "/legacy","posts/templates/"] \
         --ignore_file=["index.md"] 
```

For Confluence, you would replace the github configurations with confluence specific ones:

```yaml
# ~/decay.yml
actions: [email_owner,send_admin_report]
confluence_host: "https://myinstance.atlassian.net/wiki"
confluence_username: "myusername"
confluence_password: "<api_token>"
confluence_parent_page_id: "737509600"
administrator: "myemail@domain.com"
from_email: "noreply@domain.com"
sendgrid_api_key: "<key>"
```
```bash
~> decay 
```

## Targets

Documentation stored in Github or Confluence can be acted upon using the same general commands.  The only difference are the arguments used to point to the target documentation.  

### Github
Github documentation is identified by owner, repo and path.  So for example if you Jeff has a repo called MyDocs and he's interested in scanning everything under the "support" folder, these would be the arguments passed in:

|Property           |   Value       |
|-------------------|---------------|
| github_owner      | jeff          |
| github_repo       | MyDocs        |
| github_repo_folder| /support      |

And of course, you would need to pass in the API token to use using `github_access_token` argument.  

### Confluence
For confluence, documentation to target is identified using only the parent page ID.  A page ID is a numeric identifier
in confluence (e.g. 72172372).  Both that page and all of its children will be analyzed.  

|Property                   |   Value       |
|---------------------------|---------------|
| confluence_parent_page_id | 72172372      |

And Confluence requires a hostname (which identifies the server instance), the username and the password.  The password
must be the user's API token - not the actual login password used to access the UI.

## Actions

Decay can perform multiple actions either in one command run or separately as part of a series of commands. The actions to perform are:

### `email_owner`
Sends a single message containing a list of all the documents that are fall outside of the "fresh" range of dates specified in the configuration.  For example, if you have set `STALE_AGE_IN_DAYS` to 30 and a doc has not been updated in 31 then an email will be sent to the owner of that file.  If no owner has been specified then the administrator will be notified. If no admin has been passed into the command then an error message will be shown during command run.

**Required arguments:**
* from_email
* sendgrid_api_key

### `send_admin_report`
Send a single email to the administrator with a list of all the documents being reviewed along with the age and the last editor of each.  This is meant to be used to provide a full state of documentation for a given repo (or sub-repo).

**Required arguments:**
* administrator
* from_email
* sendgrid_api_key

### `mark`
Rather than sending an email to owners or administrators, this will update the document itself with the new state.  For example, if the doc has not be updated in over `STALE_AGE_IN_DAYS` then `out_of_date` will be set to `true`.  

Each file updated is done as a separate commit - for that reason, it makes the changes in a separate branch then opens a PR against the source branch specified in the `github_branch` argument.  By default, this will be `master`.  

It is recommended that when merging the PR that you use the `Squash and Merge` option - especially if a lot of files have changed.

**Required arguments:**
* _None_


## File Types
While it is designed to help identify stale documentation, it can be used for any type of file within a given root. By default it looks for markdown and html files.  But you can change the file types using the `--extensions` argument.  

## Owners
In the decay parlance, an owner is anyone who is responsible for keeping documentation up to date.  Not all documentation has an owner.  In the cases where no owner is found and an administrator has been specified, then the admin is assumed to be the owner.

To specify an owner, the document must have a frontmatter section at the top of the file.  In that frontmatter, you must specify an "owner" which is an email address.  It is this email that is used to send owner reports.

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
There is also the notion of an administrator.  An administrator is the person who is responsible for the body of documentation being analyzed.  An admin and an owner can be the same person if there is no specific owner specified for a given document.  In fact, if a report is requested for 'owners' then the admin is assumed if no owner is specified (see _Reports_ below).

## Reports
There are two types of reports: owner and admin.  

### Owner Report
The owner report is sent to anyone who is marked as an owner of at least one document that is beginning to decay.  For example, if there is a folder that looks like this:

```
+ docs
    - index.md (owner is bob@email.com, decaying)
    - info.md  (owner is bob@email.com)
    - access.md(owner is john@email.com, decaying)
```

In this case, two owner reports will be sent out.  The first will contain exactly one file (index.md) and be sent to bob@.  The other will contain only file and will be sent to john@.  Notice that info.md is not sent anywhere because it hasn't be tagged as decaying. 

### Admin Report
The admin report is sent to the administrator after command execution.  Unlike the owner report, this report contains information about every document in the body of documentation being examined.  Information in the report includes things like document age, last editor, etc.


  
## Arguments

Arguments can be provided either on the command line, in environment variables or in a YAML file called `decay.yml` in the current working directory.  You can also specify a config file to use with the `-c` or `--config` argument.  The order of preference for configuration variables is:

1. Command-line
2. Environment
3. Config File

```
usage: main.py [-h] [-c CONFIG] -o GITHUB_OWNER [-i IGNORE_PATHS]
               [-n IGNORE_FILES] -g GITHUB_REPO -f GITHUB_REPO_FOLDER
               [-b GITHUB_BRANCH] -a GITHUB_ACCESS_TOKEN
               [-s STALE_AGE_IN_DAYS] [-k SENDGRID_API_KEY] [-r FROM_EMAIL]
               [-x EXTENSIONS] [-m ADMINISTRATOR]
               ACTION [ACTION ...]

Generate reports on documentation decay Args that start with '--' (eg. -o) can
also be set in a config file (./decay.yml or specified via -c). The config
file uses YAML syntax and must represent a YAML 'mapping' (for details, see
http://learn.getgrav.org/advanced/yaml). If an arg is specified in more than
one place, then commandline values override config file values which override
defaults.

positional arguments:
  ACTION

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to YAML configuration file
  -o GITHUB_OWNER, --github_owner GITHUB_OWNER
                        The organization name is the owner
  -i IGNORE_PATHS, --ignore_path IGNORE_PATHS
                        Use this for each path that should be skipped by the
                        decay detector.
  -n IGNORE_FILES, --ignore_file IGNORE_FILES
                        Use this for each file that should be skipped by the
                        decay detector. This should be the path to the file in
                        the repo.
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
  -k SENDGRID_API_KEY, --sendgrid_api_key SENDGRID_API_KEY
                        This is the sendgrid api key to use when an action is
                        being performed that requires emailto be sent. This IS
                        required if one of the actions requested requires
                        email sending.
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
```

## Development

To prepare for development you must have pipenv:

```
~> pipenv install
```

To deploy, first change the version number in setup.py then:

```
~> python setup.py sdist
~> python -m twine upload dist/*
```
