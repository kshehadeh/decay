import datetime
from typing import List

from decay.analyzers import FileAnalysis
from decay.context import DocCheckerContext, ACTION_EMAIL_OWNER, ACTION_SEND_ADMIN_REPORT
from decay.feedback import warning, info
from decay.reports import OwnerReport, AdminReport


def send_results(all_file_analyses: List[FileAnalysis], context: DocCheckerContext):

    if context.should_take_action(ACTION_EMAIL_OWNER):
        results = {}
        info(f"Preparing to send email to owners for {len(all_file_analyses)} documents...", 0)

        # Group all the analyses into lists under each email recipient.
        for a in all_file_analyses:
            if not a.file_changed_recently:
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

    if context.should_take_action(ACTION_SEND_ADMIN_REPORT):
        info(f"Preparing to send the administrator report via email for {len(all_file_analyses)} documents...", 0)
        admin_report = AdminReport([context.administrator], context)
        admin_report.add_analysis(all_file_analyses)
        admin_report.send()


