# -*- coding: utf-8 -*-

import configargparse

from decay.markers.github import mark_github_files
from decay.markers.confluence import mark_confluence_files
from decay.analyzers.github import analyze_github_path
from decay.analyzers.confluence import analyze_confluence_page_tree
from decay.comms import send_results
from decay.context import DocCheckerContext, ACTIONS
from decay.feedback import error


def get_parser():
    # parser = argparse.ArgumentParser(description="Generate reports on documentation decay")
    parser = configargparse.ArgumentParser(

        description="Generate reports on documentation decay",
        default_config_files=["./decay.yml"],
        config_file_parser_class=configargparse.YAMLConfigFileParser
    )

    parser.add_argument('actions', metavar='ACTION', type=str, nargs='+', choices=ACTIONS)

    parser.add_argument('-c', '--config', required=False, is_config_file=True,
                        help='Path to YAML configuration file')

    # PROCESSING OPTIONS
    parser.add_argument('-s', '--stale_age_in_days', dest="stale_age_in_days", default=30, type=int,
                        help="The number of days of no activity after which a file is considered to be stale.")
    parser.add_argument('-x', '--extensions', dest="extensions", required=False, default=".md,.html",
                        help="These are the file extensions that will be checked within the given root")
    parser.add_argument('-i', '--ignore_path', action='append', dest="ignore_paths", required=False,
                        help="Use this for each path that should be skipped by the decay detector.")
    parser.add_argument('-n', '--ignore_file', action='append', dest="ignore_files", required=False,
                        help="Use this for each file that should be skipped by the decay detector.  This should be "
                             "the path to the file in the repo.")

    # CONFLUENCE OPTIONS
    parser.add_argument('--confluence_hostname', dest="confluence_hostname", required=False,
                        help="The hostname of the confluence instance (e.g. https://myinstance.atlassian.net)")
    parser.add_argument('--confluence_username', dest="confluence_username", required=False,
                        help="In most cases, this is an email address")
    parser.add_argument('--confluence_password', dest="confluence_password", required=False,
                        help="In the latest version of Confluence, your password must be a generate API token - not "
                             "your actual password")
    parser.add_argument('--confluence_parent_page_id', dest="confluence_parent_page_id", required=False,
                        help="The parent page under which pages should be analyzed.")

    # GITHUB OPTIONS
    parser.add_argument('-o', '--github_owner', dest="github_owner", required=False,
                        help="The organization name is the owner")
    parser.add_argument('-g', '--github_repo', dest="github_repo", required=False,
                        help="The repository name (excluding the path)")
    parser.add_argument('-f', '--github_repo_folder', dest="github_repo_folder", required=False,
                        help="The path of the file in the repo - starting without a leading slash")
    parser.add_argument('-b', '--github_branch', dest="github_branch", default="master",
                        help="The branch to use for the repo - uses 'master' by default.")
    parser.add_argument('-a', '--github_access_token', dest="github_access_token", required=False,
                        help="The personal access token to use - keeping in mind that the token needs to have access "
                             "to any SSO-protected repo")

    # EMAIL  OPTIONS
    parser.add_argument('-k', '--sendgrid_api_key', dest="sendgrid_api_key", required=False,
                        help="This is the sendgrid api key to use when an action is being performed that requires email"
                             "to be sent. This IS required if one of the actions requested requires email sending.")
    parser.add_argument('-r', '--from_email', dest="from_email", required=False, default="noreply@underarmour.com",
                        help="This is the email that sent emails will appear to come from")

    parser.add_argument('-m', '--administrator', dest="administrator", required=False,
                        help="The admin will receive the admin report (if arg set) and any emails that would be sent "
                             "to an owner - but one does not exist.")
    return parser


def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(args=argv)
    ctx = DocCheckerContext(args, parser)
    analyzed_results = None
    if ctx.github:
        analyzed_results = analyze_github_path(ctx.github_repo_path, ctx)
        mark_github_files(analyzed_results, ctx)
    elif ctx.confluence:
        analyzed_results = analyze_confluence_page_tree(ctx.confluence_parent_page_id, ctx)
        mark_confluence_files(analyzed_results, ctx)
    else:
        error("Unable to determine which documentation source to analyze.", 0)
        exit(1)

    if analyzed_results:
        send_results(analyzed_results, ctx)


if __name__ == "__main__":
    main()
