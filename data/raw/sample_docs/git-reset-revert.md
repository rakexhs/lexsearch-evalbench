# Undoing Changes in Git: reset, revert, restore

<!-- category: version-control -->

## git restore
`git restore <file>` discards uncommitted changes in the working directory for that
file. Use `git restore --staged <file>` to unstage a file without losing its edits.

## git reset
`git reset` moves the current branch tip. `--soft` keeps changes staged, `--mixed`
(the default) keeps changes in the working tree but unstages them, and `--hard`
discards all changes. Because `--hard` is destructive, it should be used with care.

## git revert
`git revert <commit>` creates a new commit that undoes the changes of an earlier
commit without rewriting history. This is the safe way to undo a change that has
already been shared, since it does not alter existing commit hashes.
