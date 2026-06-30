# Tagging Releases in Git

<!-- category: version-control -->

## Lightweight vs annotated tags
A Git tag marks a specific commit, typically a release point. A lightweight tag is
just a named pointer to a commit, while an annotated tag is a full object storing a
message, tagger, and date. Create an annotated tag with `git tag -a v1.0 -m "release"`.

## Pushing tags
Tags are not pushed by default when you push a branch. Push a single tag with
`git push origin v1.0`, or push every tag at once with `git push --tags`.

## Checking out a tag
Checking out a tag puts you in a detached HEAD state because a tag is not a moving
branch pointer. To continue work, create a branch from the tag first.
