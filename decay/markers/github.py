from typing import List
import datetime
from os.path import basename
from github import PullRequest, GitRef, ContentFile
import frontmatter

from decay.feedback import error
from decay.analyzers import FileAnalysis
from decay.context import DocCheckerContext, ACTION_MARK


def create_ref(ctx: DocCheckerContext) -> GitRef:
    branch_name = "decay-marker-" + str(datetime.datetime.now().timestamp())
    source_branch = ctx.repo_ob.get_branch(ctx.github_branch)
    return ctx.repo_ob.create_git_ref(ref=f'refs/heads/{branch_name}', sha=source_branch.commit.sha)


def mark_github_files(all_file_analyses: List[FileAnalysis], ctx: DocCheckerContext) -> PullRequest:
    """
    This will update the given file in the repository based on the results of the file analyses.  It will create
    multiple commits but assemble them together into a PR which can be squashed before merge (manually).
    :param all_file_analyses: All the results of the file analsis phase
    :param ctx:
    :return: Returns a PR if changes were made as a result of the file analyses, otherwise returns None.
    """
    ref = None
    if ctx.should_take_action(ACTION_MARK):

        # first create a new branch for all the changes to be made in
        commits = []
        for file in all_file_analyses:
            new_commit = update_file(ctx, file)
            if new_commit:
                commits.append(new_commit)

        if len(commits) > 0:
            new_pr = ctx.repo_ob.create_pull(title="Decay automated updates",
                                             body="This PR was generated automatically by Decay because properties on "
                                                  "some files were changed.",
                                             head=basename(ctx.ref_with_changes.ref), base=ctx.github_branch)
            return new_pr
        else:
            return None


def update_file(ctx, file):

    # we will add to this dict as we determine that there
    #   are properties that need to be changed.  If, at the end,
    #   we have no changed properties, then we will do nothing with the file in
    #   the source repo.
    props_to_change = {}

    # Check `out_of_date` property.
    if not file.file_changed_recently:
        props_to_change = {
            "out_of_date": True
        }

    if len(props_to_change) == 0:
        return None

    gh_file: ContentFile = ctx.repo_ob.get_contents(file.file_identifier)
    parsed = frontmatter.loads(gh_file.decoded_content)
    changed = False

    # Okay, we have determined that one or more properties should be set to a certain value.  Now
    #   let's load the content from the repo and see if any of these properties are different
    #   than what's already there.  If not, we will not make any changes and exit the function.
    for k, v in props_to_change.items():
        if (k in parsed and parsed[k] != v) or k not in parsed:
            parsed[k] = v
            changed = True

    if changed:
        if not ctx.ref_with_changes:
            # if we haven't created the branch, do so now.  We wait to create in case
            #   there are no changes that need to be made.
            ctx.ref_with_changes = create_ref(ctx)

        if not ctx.ref_with_changes:
            # something went wrong
            error("There was a problem while creating a branch to host marker changes", 1)

        new_commit, _ = ctx.repo_ob.update_file(path=file.file_identifier,
                                                message="decay updated these fields: " + ",".join(
                                                    props_to_change.keys()),
                                                content=frontmatter.dumps(parsed),
                                                sha=gh_file.sha,
                                                branch=basename(ctx.ref_with_changes.ref))

        return new_commit
    else:

        # Nothing changed so skip
        return None
