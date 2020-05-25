# decay
This tool will validate that a given folder within a git repository contains documents that have been updated within a set period of time. The intention is to help keep documentation as fresh as possible.  After `STALE_AGE_IN_DAYS` days have passed since the last commit, the document is said to beging decaying.    

## Usage
This script is meant to be used as part of a CI process such as Github Actions or Circle CI.  

### File Types
While it is designed to help identify stale documentation, it can be used for any type of file within a given root. By default it looks for markdown and html files.  But you can change the file types using the `--extensions` argument.  

### Owners
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

### Administrator
There is also the notion of an administrator.  The administrator is the person that, if `email_owner` is set but an owner could not be found, will receive the notification emails.  If `send_admin_report` is true then the administrator will also receive a report of all the files that were checked, their age, which are now considered stale and who the last person to change the file was.

### Reports
There are two types of reports: owner and admin.  

The owner report is sent to anyone who is marked as an owner of at least one document that is beginning to decay.  For example, if there is a folder that looks like this:

```
+ docs
    - index.md (owner is bob@email.com, decaying)
    - info.md  (owner is bob@email.com)
    - access.md(owner is john@email.com, decaying)
```

In this case, two owner reports will be sent out.  The first will contain exactly one file (index.md) and be sent to bob@.  The other will contain only file and will be sent to john@.  Notice that info.md is not sent anywhere because it hasn't be tagged as decaying. 


  
### Arguments
```
usage: main.py [-h] -o GITHUB_OWNER -g GITHUB_REPO -f GITHUB_REPO_FOLDER
               [-b GITHUB_BRANCH] -a GITHUB_ACCESS_TOKEN
               [-s STALE_AGE_IN_DAYS] [-e EMAIL_OWNER] [-k SENDGRID_API_KEY]
               [-r FROM_EMAIL]

Generate documentation map for TOC

optional arguments:
  -h, --help            show this help message and exit
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
```
