from argparse import ArgumentParser
import argparse

from pyfluence import Confluence

from email_validator import validate_email, EmailNotValidError
from github import Github, Repository, GitRef

from decay.feedback import error
from decay.util import remove_leading_trailing_slashes

ACTION_EMAIL_OWNER = 'email_owner'
ACTION_SEND_ADMIN_REPORT = 'send_admin_report'
ACTION_MARK = 'mark'

ACTIONS = [ACTION_EMAIL_OWNER, ACTION_SEND_ADMIN_REPORT, ACTION_MARK]


class DocCheckerContext:
    def __init__(self, args: argparse.Namespace, parser: ArgumentParser):
        self.github = None
        self.confluence = None

        self.actions = args.actions
        self.github_branch = args.github_branch
        self.github_repo = args.github_repo
        self.github_repo_owner = args.github_owner
        self.github_repo_path = args.github_repo_folder
        self.github_token = args.github_access_token
        self.confluence_hostname = args.confluence_hostname
        self.confluence_username = args.confluence_username
        self.confluence_password = args.confluence_password
        self.confluence_parent_page_id = args.confluence_parent_page_id

        self.doc_is_stale_after_days = args.stale_age_in_days
        self.sendgrid_api_key = args.sendgrid_api_key
        self.from_email = args.from_email
        self.administrator = args.administrator
        self.extensions = args.extensions.split(",")
        self.ignore_paths = list(
            map(lambda x: remove_leading_trailing_slashes(x), args.ignore_paths)) if args.ignore_paths else []
        self.ignore_files = list(
            map(lambda x: remove_leading_trailing_slashes(x), args.ignore_files)) if args.ignore_files else []
        self.ref_with_changes: GitRef = None

        if ACTION_SEND_ADMIN_REPORT in self.actions and not self.administrator:
            parser.error(
                "With the send_admin_report action, you must specify an administrator email using 'administrator' "
                "argument")

        if self.administrator:
            try:
                valid = validate_email(self.administrator)
                self.administrator = valid.email
            except EmailNotValidError as e:
                parser.error(f"{self.administrator} is not a valid email address: " + str(e))

        if self.from_email:
            try:
                valid = validate_email(self.from_email)
                self.from_email = valid.email
            except EmailNotValidError as e:
                parser.error(f"{self.from_email} is not a valid email address: " + str(e))

        if ACTION_EMAIL_OWNER in self.actions or ACTION_SEND_ADMIN_REPORT in self.actions:
            if not self.sendgrid_api_key:
                parser.error(f"You must specify a sendgrid token if you are sending owner or admin reports via email")

            if not self.from_email:
                parser.error(f"You must specify a 'from' email if you are sending owner or admin reports via email")

        if self.github_token:
            if not self.github_repo_owner or not self.github_repo:
                parser.error(f"If you are analyzing a github repo, you must specify the owner and repo")

            elif not self.github_repo_path:
                parser.error(
                    f"If you are analyzing a github repo, you must specify the path to start the analysis in (can be "
                    f"'/')")

            else:
                self.github = Github(login_or_token=self.github_token, per_page=10)
                self.repo_ob: Repository = self.github.get_repo(f"{self.github_repo_owner}/{self.github_repo}")
                if not self.repo_ob:
                    error(f"Unable to find the {self.github_repo_owner}/{self.github_repo} repo.")

        if self.confluence_password:
            try:
                self.confluence = Confluence(self.confluence_username, self.confluence_password,
                                             self.confluence_hostname)
            except Exception as e:
                error(f"Unable to establish a connection to Confluence: " + str(e))

    def should_take_action(self, action):
        return action in self.actions
