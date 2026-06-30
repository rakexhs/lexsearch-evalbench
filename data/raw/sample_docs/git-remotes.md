# Working with Git Remotes: fetch, pull, push

<!-- category: version-control -->

## Remotes
A remote is a named reference to another copy of the repository, conventionally
called `origin`. `git remote -v` lists the configured remotes and their URLs.

## fetch vs pull
`git fetch` downloads new commits and updates remote-tracking branches without
changing your working branch. `git pull` is `git fetch` followed by a merge (or a
rebase with `--rebase`) into your current branch, so it can create merge commits.

## push
`git push origin main` uploads your local commits on `main` to the remote. A push is
rejected when the remote has commits you do not have locally; fetch and integrate
them first before pushing again.
