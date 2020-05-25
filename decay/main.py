import datetime
import os

from typing import List, Union

import frontmatter
import argparse
from github import Github, Repository
import sendgrid
from markdown2 import Markdown
from email_validator import validate_email, EmailNotValidError

owner_subject_template = "Documentation Checker Owner Report - {stale_doc_count} docs found that are more than {" \
                         "stale_doc_days} days old"
admin_subject_template = "Documentation Checker Admin Report"
line_item_template = "| {file_path} | {stale_days} | {changed_by} | [{file_link}]({file_link}) |"
body_template = \
    """
## Documentation Report

### Stale Docs

| Path   | Age (Days) | Changed By | Link      |
|--------|------------|------------| ----------|
{item_list}



### Parameters 

| Github Repo   | Repo Root          | Max Age          |
|---------------|--------------------|------------------|
| {github_repo} | {github_repo_root} | {max_stale_days} |
"""

css = \
    """
<style>
    tr:nth-child(even){
        background: #efefef;
    }
    
    th {
        font-weight:bold;
        text-align:left;
        border-bottom: 1px solid #333
    }
    
    th, td {
        padding: 7px;
    }
</style>
"""


def generic_msg(msg, indent=0):
    print((indent * 2) * ' ' + msg)


def info(msg, indent=0):
    if indent == 0:
        generic_msg("🚩 " + msg, 0)
    else:
        generic_msg("→ " + msg, indent)


def success(msg, indent=0):
    generic_msg("✅ " + msg, indent)


def warning(msg, indent=0):
    generic_msg("⚠️ " + msg, indent)


def error(msg, indent=0):
    generic_msg("❌ " + msg, indent)


class DocCheckerContext:
    def __init__(self, args: argparse.Namespace):
        self.github_branch = args.github_branch
        self.github_repo = args.github_repo
        self.github_repo_owner = args.github_owner
        self.github_repo_path = args.github_repo_folder
        self.github_token = args.github_access_token
        self.doc_is_stale_after_days = args.stale_age_in_days
        self.email_owner_if_stale = args.email_owner
        self.sendgrid_api_key = args.sendgrid_api_key
        self.from_email = args.from_email
        self.admin_report = args.admin_report
        self.administrator = args.administrator
        self.extensions = args.extensions.split(",")

        if not self.sendgrid_api_key and self.email_owner_if_stale:
            raise argparse.ArgumentError(
                "❌ You must specify a sendgrid API key if you want to email owners when stale.")

        if self.admin_report is True and not self.administrator:
            raise argparse.ArgumentError(
                "❌ With 'admin_report' set, you must specify an administrator email using 'administrator' argument")

        if self.administrator:
            try:
                valid = validate_email(self.administrator)
                self.administrator = valid.email
            except EmailNotValidError as e:
                raise argparse.ArgumentError(f"{self.administrator} is not a valid email address: " + str(e))


class FileAnalysis(object):
    def __init__(self):
        self._file_link: str = ""
        self._file_path: str = ""
        self._file_changed_recently: bool = True
        self._last_change: Union[datetime.datetime, None] = None
        self._changed_by: Union[str, None] = None
        self._owner: str = ""

    @property
    def file_link(self) -> str:
        return self._file_link

    @file_link.setter
    def file_link(self, val: str):
        self._file_link = val

    @property
    def changed_by(self) -> Union[str, None]:
        return self._changed_by

    @changed_by.setter
    def changed_by(self, val: Union[str, None]):
        self._changed_by = val

    @property
    def last_change(self) -> Union[datetime.datetime, None]:
        return self._last_change

    @last_change.setter
    def last_change(self, val: Union[datetime.datetime, None]):
        self._last_change = val

    @property
    def file_path(self) -> str:
        return self._file_path

    @file_path.setter
    def file_path(self, val: str):
        self._file_path = val

    @property
    def file_changed_recently(self) -> bool:
        return self._file_changed_recently

    @file_changed_recently.setter
    def file_changed_recently(self, val: bool):
        self._file_changed_recently = val

    @property
    def owner(self) -> str:
        return self._owner

    @owner.setter
    def owner(self, val: str):
        self._owner = val


class DocReport(object):
    def __init__(self, recipients: List[str], context: DocCheckerContext):
        self.context: DocCheckerContext = context
        self.recipients: List[str] = recipients
        self.analyses: List[FileAnalysis] = []

    def title(self):
        raise NotImplemented()

    def subject(self):
        raise NotImplemented()

    def add_analysis(self, analysis: Union[List[FileAnalysis], FileAnalysis]):
        if isinstance(analysis, list):
            self.analyses = [*self.analyses, *analysis]
        else:
            self.analyses.append(analysis)

    def send(self):
        sg = sendgrid.SendGridAPIClient(api_key=self.context.sendgrid_api_key)
        markdowner = Markdown(extras=["tables"])

        from_email = sendgrid.Email(self.context.from_email)
        body = []
        for a in self.analyses:
            stale_days = (datetime.datetime.now() - a.last_change).days if a.last_change else "Never updated"
            body.append(line_item_template.format(file_path=a.file_path, file_link=a.file_link,
                                                  changed_by=a.changed_by, stale_days=stale_days))

        plain_text = body_template.format(item_list="\n".join(body),
                                          github_repo=self.context.github_repo,
                                          github_repo_root=self.context.github_repo_path,
                                          max_stale_days=self.context.doc_is_stale_after_days)
        html_text = markdowner.convert(plain_text)

        content_text = sendgrid.Content("text/plain", plain_text)
        content_html = sendgrid.Content("text/html", html_text + "\n" + css)

        recipients = list(map(lambda x: sendgrid.To(x), self.recipients))
        mail = sendgrid.Mail(from_email, recipients, self.subject(), plain_text_content=content_text,
                             html_content=content_html)
        response = sg.client.mail.send.post(request_body=mail.get())

        if 300 > response.status_code >= 200:
            success(f"Successfully sent email to {', '.join(self.recipients)} regarding {len(self.analyses)} files", 2)
        else:
            error(
                f"Failed to send email to {', '.join(self.recipients)} regarding {len(self.analyses)} files: "
                f"{response.status_code} - {response.body}", 2)


class OwnerReport(DocReport):
    def title(self):
        return "Documentation Owner Report"

    def subject(self):
        return owner_subject_template.format(stale_doc_count=len(self.analyses),
                                             stale_doc_days=self.context.doc_is_stale_after_days)


class AdminReport(DocReport):
    def title(self):
        return "Documentation Admin Report"

    def subject(self):
        return admin_subject_template


def analyze_file(repo: Repository, path_to_file: str, context: DocCheckerContext) -> FileAnalysis:
    """
    This will actually load the file and the commit information to get things like if it was changed recently
    and who the owner (is taken from the frontmatter).
    :param context:
    :param repo: The repo object in the API client
    :param path_to_file: The path to the file in the repo (as in "lib/myfile.md")
    :return:
    """
    analysis = FileAnalysis()

    info(f"Checking file {path_to_file}...")
    try:
        commits = repo.get_commits(path=path_to_file)
        no_earlier_than = datetime.datetime.now() - datetime.timedelta(days=context.doc_is_stale_after_days)
        if commits.totalCount > 0:
            commit_date = commits[0].commit.committer.date
            analysis.file_changed_recently = commit_date >= no_earlier_than
            analysis.last_change = commit_date
            analysis.changed_by = commits[0].commit.committer.email

        content = repo.get_contents(path_to_file, ref=context.github_branch)
        analysis.file_link = content.html_url
        analysis.file_path = path_to_file

        if content.decoded_content:
            doc = frontmatter.loads(content.decoded_content)
            if not doc and not doc.metadata:
                error(f"There was a problem when reading the frontmatter for {path_to_file}", 1)
            else:
                if 'owner' in doc.metadata:
                    analysis.owner = doc.metadata['owner']
                    try:
                        valid = validate_email(analysis.owner)
                        analysis.owner = valid.email
                    except EmailNotValidError as e:
                        warning(f"Found an owner but the email {analysis.owner} is not valid: " + str(e), 1)
                        analysis.owner = None

        info(f"Owner: {analysis.owner if analysis.owner else 'Not found'}", 1)
        info(f"Changed On: {analysis.last_change if analysis.last_change else 'Not found'}", 1)
        info(f"Is Stale: {'No' if analysis.file_changed_recently else 'Yes'}", 1)
        info(f"Changed By: {analysis.changed_by if analysis.changed_by else 'Not found'}", 1)

    except Exception as e:
        error(f"Unable to load analysis due to exception: {str(e)} ", 1)

    return analysis


def analyze_path(repo: Repository, path: str, context: DocCheckerContext) -> List[FileAnalysis]:
    analyses = []
    try:
        contents = repo.get_contents(path, ref=context.github_branch)
        for o in contents:
            if o.type == "file":
                _, file_extension = os.path.splitext(o.path)
                if file_extension in context.extensions:
                    analysis = analyze_file(repo, o.path, context)
                    if analysis:
                        analyses.append(analysis)

            elif o.type == "dir":
                for a in analyze_path(repo, o.path, context):
                    analyses.append(a)
    except Exception as e:
        error(f"Received exception during processing of directory {path}: {str(e)}", 1)

    return analyses


def post_process_results(all_file_analyses: List[FileAnalysis], context: DocCheckerContext):
    results = {}

    # sort in descending order by age.  If there is no date, set the date to something way in the past in the hopes
    #   that it appears near the bottom of the list.
    all_file_analyses.sort(key=lambda x: x.last_change or datetime.datetime.now() - datetime.timedelta(days=3650),
                           reverse=False)

    info(f"Post-processing {len(all_file_analyses)} checked files...", 0)
    # Group all the analyses into lists under each email recipient.
    for a in all_file_analyses:
        if not a.file_changed_recently and context.email_owner_if_stale:
            email = a.owner if a.owner else context.administrator
            if not email:
                warning(
                    "Found an old doc but there's no one to send it to.  Consider setting the --administrator "
                    "argument to ensure there is a recipient for any stale docs.", 1)
            else:
                if email not in results:
                    results[email] = []
                results[email].append(a)

    info(f"Sending {len(results)} owner report emails...", 1)
    for email, stale_file_analyses in results.items():
        owner_report = OwnerReport([email], context)
        owner_report.add_analysis(stale_file_analyses)
        owner_report.send()

    if context.administrator and context.admin_report:
        info(f"Sending admin email...", 1)
        admin_report = AdminReport([context.administrator], context)
        admin_report.add_analysis(all_file_analyses)
        admin_report.send()


def main():

    parser = argparse.ArgumentParser(description="Generate reports on documentation decay")
    parser.add_argument('-o', '--github_owner', dest="github_owner", required=True,
                        help="The organization name is the owner")
    parser.add_argument('-g', '--github_repo', dest="github_repo", required=True,
                        help="The repository name (excluding the path)")
    parser.add_argument('-f', '--github_repo_folder', dest="github_repo_folder", required=True,
                        help="The path of the file in the repo - starting without a leading slash")
    parser.add_argument('-b', '--github_branch', dest="github_branch", default="master",
                        help="The branch to use for the repo - uses 'master' by default.")
    parser.add_argument('-a', '--github_access_token', dest="github_access_token", required=True,
                        help="The personal access token to use - keeping in mind that the token needs to have access "
                             "to any SSO-protected repo")
    parser.add_argument('-s', '--stale_age_in_days', dest="stale_age_in_days", default=30, type=int,
                        help="The number of days of no activity after which a file is considered to be stale.")
    parser.add_argument('-e', '--email_owner', dest="email_owner", type=bool, default=False,
                        help="Set to 'true' if the script should email the owner of stale files.")
    parser.add_argument('-k', '--sendgrid_api_key', dest="sendgrid_api_key", required=False,
                        help="This is the sendgrid api key to use when email_owner is set to True.  This value IS "
                             "required if email_owner is set to true. ")
    parser.add_argument('-r', '--from_email', dest="from_email", required=False, default="noreply@underarmour.com",
                        help="This is the email that sent emails will appear to come from")
    parser.add_argument('-x', '--extensions', dest="extensions", required=False, default=".md,.html",
                        help="These are the file extensions that will be checked within the given root")
    parser.add_argument('-m', '--administrator', dest="administrator", required=False,
                        help="The admin will receive the admin report (if arg set) and any emails that would be sent "
                             "to an owner - but one does not exist.")
    parser.add_argument('-p', '--admin_report', dest="admin_report", required=False, default="md,html",
                        help="These are the file extensions that will be checked within the given root")
    ctx = DocCheckerContext(parser.parse_args())

    gh = Github(login_or_token=ctx.github_token, per_page=10)
    target_repo = gh.get_repo(f"{ctx.github_repo_owner}/{ctx.github_repo}")
    if not target_repo:
        error(f"Unable to find the {ctx.github_repo_owner}/{ctx.github_repo} repo.")
        exit(1)

    analyzed_results = analyze_path(target_repo, ctx.github_repo_path, ctx)
    post_process_results(analyzed_results, ctx)


if __name__ == "__main__":
    main()
