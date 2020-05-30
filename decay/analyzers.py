import os
import frontmatter
from email_validator import validate_email, EmailNotValidError
from typing import List, Union
from github import Repository
import datetime

from decay.context import DocCheckerContext
from decay.feedback import info, error, warning


class FileAnalysis(object):
    """
    File Analsysis object contains all the information that was retrieved during the analysis
    phase of document decay detection.  Reports are usually generated from this information as well
    as the aggregation of data from multiple instances of this object.
    """
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


def analyze_path(path: str, context: DocCheckerContext) -> List[FileAnalysis]:
    """
    A recursive function that will descend into a github repo's tree starting at the given path.  It will
    generate a list of FileAnalysis objects for each matching file (based on context).
    :param path: The path within the repo to start the search from.
    :param context: The context object containing all the config information as well as created Github resources.
    :return: A list of FileAnalysis objects.
    """
    analyses = []
    try:
        contents = context.repo_ob.get_contents(path, ref=context.github_branch)
        for o in contents:
            if o.type == "file":
                # We've come to a file.  Check that it's not in the ignore list and that the extension
                # matches the ones we're looking for.
                _, file_extension = os.path.splitext(o.path)
                if file_extension in context.extensions:
                    if o.path not in context.ignore_files:
                        analysis = analyze_file(context.repo_ob, o.path, context)
                        if analysis:
                            analyses.append(analysis)

            elif o.type == "dir":
                # We've come to a directory.  Check that it's not in the ignore list
                for a in analyze_path(o.path, context):
                    if o.path not in context.ignore_paths:
                        analyses.append(a)

    except Exception as e:
        error(f"Received exception during processing of directory {path}: {str(e)}", 1)

    # sort in descending order by age.  If there is no date, set the date to something way in the past in the hopes
    #   that it appears near the bottom of the list.
    analyses.sort(key=lambda x: x.last_change or datetime.datetime.now() - datetime.timedelta(days=3650),
                  reverse=False)

    return analyses
