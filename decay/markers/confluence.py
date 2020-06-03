from typing import List
# import datetime

# from decay.feedback import error
from decay.analyzers import FileAnalysis
from decay.context import DocCheckerContext, ACTION_MARK
from pyfluence import UPDATE_APPEND

TITLE_POSTFIX_OUT_OF_DATE = " (Stale)"


def mark_confluence_files(all_file_analyses: List[FileAnalysis], ctx: DocCheckerContext) -> None:
    """
    This will update the given file in the repository based on the results of the file analyses.  It will create
    multiple commits but assemble them together into a PR which can be squashed before merge (manually).
    :param all_file_analyses: All the results of the file analsis phase
    :param ctx:
    :return: Returns a PR if changes were made as a result of the file analyses, otherwise returns None.
    """
    if ctx.should_take_action(ACTION_MARK):
        for a in all_file_analyses:
            ctx.confluence.update_title(a.file_identifier, title=TITLE_POSTFIX_OUT_OF_DATE,
                                        update_type=UPDATE_APPEND)
