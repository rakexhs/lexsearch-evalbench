# Saving Work in Progress with git stash

<!-- category: version-control -->

## Purpose
`git stash` saves your uncommitted modifications (both staged and unstaged) on a
stack and reverts the working directory to a clean state, letting you switch
context without committing half-finished work.

## Common commands
`git stash push -m "message"` stashes the current changes with a label.
`git stash list` shows saved stashes. `git stash pop` reapplies the most recent
stash and removes it from the stack, while `git stash apply` reapplies it but keeps
it on the stack. Use `git stash drop` to delete a stash entry.

## Untracked files
By default stash ignores untracked files. Pass `--include-untracked` (or `-u`) to
stash untracked files as well.
