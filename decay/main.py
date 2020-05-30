# -*- coding: utf-8 -*-

import configargparse

from decay.analyzers import analyze_path
from decay.comms import send_results
from decay.context import DocCheckerContext, ACTIONS
from decay.marker import mark_files


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

    parser.add_argument('-o', '--github_owner', dest="github_owner", required=True,
                        help="The organization name is the owner")
    parser.add_argument('-i', '--ignore_path', action='append', dest="ignore_paths", required=False,
                        help="Use this for each path that should be skipped by the decay detector.")
    parser.add_argument('-n', '--ignore_file', action='append', dest="ignore_files", required=False,
                        help="Use this for each file that should be skipped by the decay detector.  This should be "
                             "the path to the file in the repo.")
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
    return parser


def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(args=argv)
    ctx = DocCheckerContext(args, parser)
    analyzed_results = analyze_path(ctx.github_repo_path, ctx)
    mark_files(analyzed_results, ctx)
    send_results(analyzed_results, ctx)


if __name__ == "__main__":
    main()
