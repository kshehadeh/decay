import datetime
from typing import List, Union

import sendgrid
from markdown2 import Markdown

from decay.analyzers import FileAnalysis
from decay.context import DocCheckerContext
from decay.feedback import success, error

owner_subject_template = "Documentation Checker Owner Report - {stale_doc_count} docs found that are more than {" \
                         "stale_doc_days} days old"
admin_subject_template = "Documentation Checker Admin Report"
line_item_template = "| {file_path} | {stale_days} | {changed_by} | [{file_link}]({file_link}) |"
body_template = \
    """
## Documentation Report

### Stale Docs

| Name   | Age (Days) | Changed By | Link      |
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
            stale_days = (datetime.datetime.now(tz=a.last_change.tzinfo) - a.last_change).days if a.last_change else "Never updated"
            body.append(line_item_template.format(file_path=a.doc_name, file_link=a.file_link,
                                                  changed_by=a.changed_by_email, stale_days=stale_days))

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
