import argparse
import pytest
from decay.main import get_parser, DocCheckerContext


def test_arg_dependencies():
    parser = get_parser()
    with pytest.raises(SystemExit):
        # missing sendgrid token but requesting email action
        args = parser.parse_args(
            ['--github_owner', 'test', '--github_repo', 'test', '--github_repo_folder', '/',
             '--email_owner', 'true', '--from_email', 'email@email.com', '--github_access_token', 'test'])
        DocCheckerContext(args,parser)

    with pytest.raises(SystemExit):
        # missing administrator but specifying admin report
        args = parser.parse_args(
            ['--github_owner', 'test', '--github_repo', 'test', '--github_repo_folder', '/',
             '--admin_report', 'true',
             '--email_owner', 'true', '--from_email', 'email@email.com', '--github_access_token', 'test',
             '--sengrid_api_key', 'test'])
        DocCheckerContext(args,parser)

    with pytest.raises(SystemExit):
        # missing from email but specifying 'email_owner'
        args = parser.parse_args(
            ['--github_owner', 'test', '--github_repo', 'test', '--github_repo_folder', '/',
             '--email_owner', 'true', '--github_access_token', 'test',
             '--sengrid_api_key', 'test'])
        DocCheckerContext(args,parser)

    with pytest.raises(SystemExit):
        # missing from email but specifying admin_report
        args = parser.parse_args(
            ['--github_owner', 'test', '--github_repo', 'test', '--github_repo_folder', '/',
             '--github_access_token', 'test',
             '--admin_report', 'true', 'administrator', 'email@email.com',
             '--sengrid_api_key', 'test'])
        DocCheckerContext(args,parser)

