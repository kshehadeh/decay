import datetime
from dateutil import tz

from typing import List

import arrow

from decay.analyzers import FileAnalysis
from decay.context import DocCheckerContext


def analyze_confluence_page_tree(page_id: str, ctx: DocCheckerContext) -> List[FileAnalysis]:

    analyses = []

    # First iterate over children
    child_pages = ctx.confluence.get_children(page_id)
    if child_pages['size'] > 0:
        children = child_pages['results']
        for child in children:
            a = analyze_confluence_page_tree(child['id'], ctx)
            analyses = a + analyses

    # Now collect information about this file.
    info = ctx.confluence.get_content(page_id)

    analysis = FileAnalysis()
    if 'version' in info:
        if 'when' in info['version']:
            docChangeDate = arrow.get(info['version']['when'])
            currentDate = datetime.datetime.now(tz=docChangeDate.tzinfo)
            analysis.last_change = docChangeDate.datetime
            earliest_change_date = currentDate - datetime.timedelta(days=ctx.doc_is_stale_after_days)
            analysis.file_changed_recently = analysis.last_change > earliest_change_date

        if 'by' in info['version']:
            analysis.changed_by_name = info['version']['by']['publicName']
            analysis.changed_by_email = info['version']['by']['email'] if 'email' in info['version']['by'] else None

    analysis.file_identifier = info['id']
    analysis.file_link = info['_links']['base'] + info['_links']['webui']
    analysis.doc_name = info['title']

    # collect all the analyses together and return them.
    analyses.append(analysis)
    return analyses
