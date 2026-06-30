# Git Branching and Merging

<!-- category: version-control -->

## Overview
A branch in Git is a lightweight movable pointer to a commit. The default branch
is named `main` in modern repositories. Creating a branch does not copy files; it
only creates a new pointer, which is why branching in Git is fast and cheap.

## Creating branches
Use `git branch <name>` to create a branch and `git switch <name>` to move onto it.
The shortcut `git switch -c <name>` creates the branch and switches in one step.
The older equivalent is `git checkout -b <name>`.

## Merging
`git merge <branch>` integrates changes from the named branch into the current
branch. When the histories have not diverged, Git performs a fast-forward merge by
simply moving the pointer forward. When both branches have new commits, Git creates
a merge commit with two parents. Conflicts must be resolved manually before the
merge commit can be completed.

## Rebasing
`git rebase <base>` replays your commits on top of another base, producing a linear
history. Unlike merging, rebasing rewrites commit hashes, so you should never rebase
commits that have already been pushed to a shared branch.
