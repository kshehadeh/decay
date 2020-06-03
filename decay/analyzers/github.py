import os
import frontmatter
from email_validator import validate_email, EmailNotValidError
from typing import List
from github import Repository
import datetime

from decay.analyzers import FileAnalysis
from decay.context import DocCheckerContext
from decay.feedback import info, error, warning


def analyze_github_file(repo: Repository, path_to_file: str, context: DocCheckerContext) -> FileAnalysis:
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
            analysis.changed_by_email = commits[0].commit.committer.email
            analysis.changed_by_name = commits[0].commit.committer.name

        content = repo.get_contents(path_to_file, ref=context.github_branch)
        analysis.file_link = content.html_url
        analysis.file_identifier = path_to_file

        if content.decoded_content:
            doc = frontmatter.loads(content.decoded_content)
            if not doc and not doc.metadata:
                error(f"There was a problem when reading the frontmatter for {path_to_file}", 1)
            else:
                if 'title' in doc.metadata:
                    analysis.doc_name = doc.metadata['title']
                else:
                    analysis.doc_name = path_to_file

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
        info(f"Changed By: {analysis.changed_by_email if analysis.changed_by_email else 'Not found'}", 1)

    except Exception as e:
        error(f"Unable to load analysis due to exception: {str(e)} ", 1)

    return analysis


def analyze_github_path(path: str, context: DocCheckerContext) -> List[FileAnalysis]:
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
                        analysis = analyze_github_file(context.repo_ob, o.path, context)
                        if analysis:
                            analyses.append(analysis)

            elif o.type == "dir":
                # We've come to a directory.  Check that it's not in the ignore list
                for a in analyze_github_path(o.path, context):
                    if o.path not in context.ignore_paths:
                        analyses.append(a)

    except Exception as e:
        error(f"Received exception during processing of directory {path}: {str(e)}", 1)

    # sort in descending order by age.  If there is no date, set the date to something way in the past in the hopes
    #   that it appears near the bottom of the list.
    analyses.sort(key=lambda x: x.last_change or datetime.datetime.now() - datetime.timedelta(days=3650),
                  reverse=False)

    return analyses
