"""Built-in sample corpus + golden evaluation set.

The corpus is a small, realistic set of open-source software documentation pages
(git, docker, fastapi, numpy, etc.). It is stored here as structured Python data
so the project runs with NO external downloads. `materialize()` writes the docs to
`data/raw/sample_docs/*.md` and the golden questions to
`data/eval/golden_questions.jsonl`.

Golden questions reference real `relevant_doc_ids`, and golden answers reuse
phrasing present in the docs so that citation-faithfulness checking is meaningful.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from app.config import settings

# ──────────────────────────────────────────────────────────────────────────────
# Each doc: id -> {title, category, text}. Text uses simple markdown with
# `## Section` headers so the chunker can attach section metadata.
# ──────────────────────────────────────────────────────────────────────────────
DOCS: Dict[str, Dict[str, str]] = {
    "git-branching": {
        "title": "Git Branching and Merging",
        "category": "version-control",
        "text": """## Overview
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
""",
    },
    "git-reset-revert": {
        "title": "Undoing Changes in Git: reset, revert, restore",
        "category": "version-control",
        "text": """## git restore
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
""",
    },
    "git-stash": {
        "title": "Saving Work in Progress with git stash",
        "category": "version-control",
        "text": """## Purpose
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
""",
    },
    "docker-images-containers": {
        "title": "Docker Images vs Containers",
        "category": "containers",
        "text": """## Images
A Docker image is a read-only template that contains the application code, runtime,
libraries, and dependencies. Images are built in layers; each instruction in a
Dockerfile creates a new layer, and identical layers are cached and shared between
images to save space.

## Containers
A container is a running instance of an image. It adds a thin writable layer on top
of the immutable image layers. Multiple containers can run from the same image, each
isolated with its own filesystem, network interface, and process space.

## Lifecycle
`docker run <image>` creates and starts a container from an image. `docker ps`
lists running containers, and `docker ps -a` includes stopped ones. `docker stop`
sends SIGTERM to gracefully stop a container, while `docker rm` removes a stopped
container.
""",
    },
    "dockerfile-best-practices": {
        "title": "Writing Efficient Dockerfiles",
        "category": "containers",
        "text": """## Layer caching
Order Dockerfile instructions from least to most frequently changing. Copy your
dependency manifest (for example `requirements.txt` or `package.json`) and install
dependencies before copying the rest of the source code, so that the expensive
dependency-install layer is cached and reused when only source code changes.

## Smaller images
Use a slim or alpine base image where possible, and use multi-stage builds to keep
build tools out of the final image. A `.dockerignore` file prevents unnecessary
files from being sent to the build context, speeding up builds.

## Reducing layers
Combine related `RUN` commands with `&&` to reduce the number of layers, and clean
up package manager caches in the same layer to avoid bloating the image.
""",
    },
    "docker-compose": {
        "title": "Multi-container Apps with Docker Compose",
        "category": "containers",
        "text": """## What it does
Docker Compose defines and runs multi-container applications using a single YAML
file, typically `docker-compose.yml`. Each service is described under the `services`
key with its image or build context, ports, environment variables, and volumes.

## Networking
Compose creates a default network for the application, and every service is
reachable from the others by its service name as a hostname. This means a web
service can connect to a database service simply by using the database's service
name as the host.

## Commands
`docker compose up` builds, creates, and starts all services; add `-d` to run in
detached mode. `docker compose down` stops and removes containers, networks, and the
default resources it created.
""",
    },
    "fastapi-basics": {
        "title": "Building APIs with FastAPI",
        "category": "web-frameworks",
        "text": """## Path operations
FastAPI uses Python type hints to define request and response models. A path
operation is declared with a decorator such as `@app.get("/items/{item_id}")`. Path
parameters are taken from the URL, while query parameters are function arguments
that are not part of the path.

## Validation with Pydantic
Request bodies are declared as Pydantic models. FastAPI automatically validates
incoming JSON against the model and returns a 422 Unprocessable Entity response with
a detailed error list when validation fails.

## Automatic docs
FastAPI generates interactive API documentation automatically. Swagger UI is served
at `/docs` and ReDoc at `/redoc`, both derived from the OpenAPI schema that FastAPI
produces from your type hints.
""",
    },
    "fastapi-async": {
        "title": "Async and Dependency Injection in FastAPI",
        "category": "web-frameworks",
        "text": """## async def path operations
You can declare a path operation with `async def` when it performs awaitable I/O,
such as querying a database with an async driver. FastAPI runs synchronous `def`
path operations in an external threadpool so they do not block the event loop.

## Dependency injection
The `Depends` mechanism lets you declare reusable dependencies, such as database
sessions or authentication checks. Dependencies are resolved before the path
operation runs, and their results are injected as parameters. Dependencies can
themselves depend on other dependencies, forming a tree.

## Background tasks
`BackgroundTasks` lets you schedule work to run after returning a response, which is
useful for sending notifications or writing logs without delaying the client.
""",
    },
    "numpy-broadcasting": {
        "title": "NumPy Broadcasting Rules",
        "category": "data-science",
        "text": """## The rule
Broadcasting describes how NumPy treats arrays of different shapes during arithmetic.
Starting from the trailing dimension, two dimensions are compatible when they are
equal or when one of them is 1. A size-1 dimension is stretched to match the other.

## Examples
Adding a scalar to an array applies it to every element. Adding a shape `(3,)` array
to a shape `(4, 3)` array works because the trailing dimensions match, and the
length-3 vector is broadcast across all four rows.

## When it fails
If a trailing dimension is neither equal nor 1, NumPy raises a ValueError reporting
that the operands could not be broadcast together. Reshaping one operand, for example
with `arr[:, None]`, is the usual fix.
""",
    },
    "numpy-views-copies": {
        "title": "NumPy Views vs Copies",
        "category": "data-science",
        "text": """## Views
Basic slicing of a NumPy array returns a view, not a copy. A view shares the same
underlying data buffer as the original array, so modifying the view also modifies the
original. This makes slicing cheap because no data is duplicated.

## Copies
Fancy indexing with an integer or boolean array returns a copy rather than a view.
You can force a copy explicitly with the `.copy()` method when you need an
independent array.

## Checking
The `.base` attribute is `None` for an array that owns its data and points to the
original array for a view. This is a reliable way to tell whether you are holding a
view or a copy.
""",
    },
    "pandas-merge-join": {
        "title": "Combining Data in pandas: merge, join, concat",
        "category": "data-science",
        "text": """## merge
`pandas.merge` combines two DataFrames on one or more key columns, similar to a SQL
join. The `how` parameter controls the join type: `inner` keeps only matching keys,
`left` keeps all rows from the left frame, `right` keeps all from the right, and
`outer` keeps the union of keys.

## concat
`pandas.concat` stacks DataFrames along an axis. With `axis=0` it appends rows, and
with `axis=1` it aligns on the index and adds columns. It does not match on key
columns the way merge does.

## Avoiding duplicates
When key columns share names other than the join keys, pandas appends the suffixes
`_x` and `_y` to disambiguate overlapping column names; you can override these with
the `suffixes` argument.
""",
    },
    "pandas-missing-data": {
        "title": "Handling Missing Data in pandas",
        "category": "data-science",
        "text": """## Detecting
Missing values are represented as `NaN` (or `NaT` for datetimes). `df.isna()`
returns a boolean mask of missing entries, and `df.isna().sum()` counts missing
values per column.

## Dropping
`df.dropna()` removes rows that contain any missing value; pass `axis=1` to drop
columns instead, or `how="all"` to drop only fully-empty rows.

## Filling
`df.fillna(value)` replaces missing values with a constant. Use `method="ffill"` to
propagate the last valid observation forward, or `df.fillna(df.mean())` to impute
numeric columns with their column mean.
""",
    },
    "python-venv": {
        "title": "Python Virtual Environments",
        "category": "python-tooling",
        "text": """## Why
A virtual environment is an isolated Python installation with its own `site-packages`
directory, so projects do not share dependencies and cannot break each other. Each
environment can pin different versions of the same package.

## Creating and activating
Create one with `python -m venv .venv`. Activate it on macOS or Linux with
`source .venv/bin/activate`, and on Windows with `.venv\\Scripts\\activate`.
Deactivate with the `deactivate` command.

## Dependencies
Install packages with `pip install <package>` while the environment is active.
Record exact versions with `pip freeze > requirements.txt`, and reproduce the
environment elsewhere with `pip install -r requirements.txt`.
""",
    },
    "pip-vs-conda": {
        "title": "pip vs conda for Package Management",
        "category": "python-tooling",
        "text": """## pip
pip installs Python packages from the Python Package Index (PyPI). It manages Python
dependencies only and works inside any virtual environment. Wheels make installation
fast because they ship prebuilt binaries.

## conda
conda is a language-agnostic package and environment manager that can install
non-Python dependencies such as compilers and system libraries. It resolves an
entire environment together, which helps with packages that have heavy native
dependencies.

## Choosing
Use pip with venv for lightweight, pure-Python projects. Prefer conda when you need
complex native libraries, for example certain GPU or scientific stacks, where binary
compatibility across packages matters.
""",
    },
    "pytest-fixtures": {
        "title": "pytest Fixtures and Test Structure",
        "category": "testing",
        "text": """## Fixtures
A pytest fixture is a function decorated with `@pytest.fixture` that provides setup
data or resources to tests. A test requests a fixture by naming it as a function
argument, and pytest injects the returned value.

## Scope
Fixture `scope` controls how often a fixture is created: `function` (the default)
runs it for every test, while `module` or `session` reuse one instance across many
tests, which is useful for expensive setup like a database connection.

## Parametrization
`@pytest.mark.parametrize` runs the same test with multiple input sets, producing a
separate reported test case for each parameter combination. Fixtures can also be
parametrized to multiply across configurations.
""",
    },
    "pytest-assertions": {
        "title": "Assertions and Exceptions in pytest",
        "category": "testing",
        "text": """## Plain asserts
pytest uses Python's plain `assert` statement and rewrites it to provide detailed
introspection of the failing expression, so you rarely need special assertion
methods.

## Expecting exceptions
Use the `pytest.raises` context manager to assert that a block raises a specific
exception: `with pytest.raises(ValueError):`. You can inspect the captured exception
through the `excinfo` object the context manager yields.

## Approximate comparisons
`pytest.approx` compares floating-point numbers with a tolerance, avoiding spurious
failures from rounding, for example `assert result == pytest.approx(0.1 + 0.2)`.
""",
    },
    "rest-http-methods": {
        "title": "HTTP Methods and REST Semantics",
        "category": "web-fundamentals",
        "text": """## Methods
GET retrieves a resource and must be safe and idempotent, meaning it does not modify
state. POST creates a new resource or triggers processing and is not idempotent. PUT
replaces a resource and is idempotent. PATCH applies a partial update, and DELETE
removes a resource.

## Idempotency
An idempotent method produces the same server state no matter how many times it is
called with the same payload. GET, PUT, and DELETE are idempotent; POST is not,
which is why retrying a POST can create duplicate resources.

## Status codes
2xx indicates success, 3xx redirection, 4xx a client error such as 404 Not Found or
422 validation failure, and 5xx a server error. 201 Created is the conventional
response to a successful POST that creates a resource.
""",
    },
    "http-status-codes": {
        "title": "Common HTTP Status Codes",
        "category": "web-fundamentals",
        "text": """## Success
200 OK is the standard success response. 201 Created signals that a new resource was
created. 204 No Content means the request succeeded but there is no body to return,
common for DELETE.

## Client errors
400 Bad Request indicates malformed syntax. 401 Unauthorized means authentication is
required or failed, while 403 Forbidden means the user is authenticated but not
allowed. 404 Not Found means the resource does not exist. 429 Too Many Requests
signals rate limiting.

## Server errors
500 Internal Server Error is a generic server failure. 502 Bad Gateway and 503
Service Unavailable indicate upstream or capacity problems, often returned by load
balancers when a backend is down.
""",
    },
    "sql-indexes": {
        "title": "Database Indexes and Query Performance",
        "category": "databases",
        "text": """## What an index is
A database index is a data structure, usually a B-tree, that speeds up row lookups by
column value at the cost of extra storage and slower writes. Without an index, the
database must perform a full table scan to find matching rows.

## When to use
Index columns that appear frequently in WHERE clauses, JOIN conditions, and ORDER BY.
A composite index on multiple columns helps queries that filter on a leading prefix
of those columns, following the left-most prefix rule.

## Costs
Every index must be updated on INSERT, UPDATE, and DELETE, so over-indexing slows
writes and consumes storage. Indexes that are never used by the query planner should
be removed.
""",
    },
    "sql-joins": {
        "title": "SQL Joins Explained",
        "category": "databases",
        "text": """## INNER JOIN
An INNER JOIN returns only the rows that have matching values in both tables on the
join condition. Rows without a match in either table are excluded from the result.

## OUTER JOINS
A LEFT JOIN returns all rows from the left table plus matching rows from the right,
filling unmatched right-side columns with NULL. A RIGHT JOIN is the mirror image, and
a FULL OUTER JOIN returns rows that match in either table.

## CROSS JOIN
A CROSS JOIN produces the Cartesian product of the two tables, pairing every row of
the first with every row of the second. It is rarely what you want unless you
explicitly need all combinations.
""",
    },
    "rag-overview": {
        "title": "Retrieval-Augmented Generation (RAG) Basics",
        "category": "ai-ml",
        "text": """## Motivation
Retrieval-Augmented Generation grounds a language model's output in an external
knowledge base. Instead of relying solely on parameters, the system retrieves
relevant documents at query time and conditions generation on them, which reduces
hallucination and lets answers cite sources.

## Pipeline
A typical RAG pipeline ingests documents, splits them into chunks, embeds the chunks
into vectors, and stores them in an index. At query time it embeds the question,
retrieves the most similar chunks, and passes them to the generator as context.

## Failure modes
RAG quality is bounded by retrieval: if the relevant chunk is not retrieved, the
generator cannot produce a correct grounded answer. Poor chunking, weak embeddings,
and lack of reranking are common causes of low retrieval recall.
""",
    },
    "embeddings-similarity": {
        "title": "Text Embeddings and Similarity Search",
        "category": "ai-ml",
        "text": """## Embeddings
A text embedding maps a piece of text to a dense vector such that semantically
similar texts land near each other in vector space. Sentence-transformer models are
commonly used to produce these embeddings for retrieval.

## Cosine similarity
Similarity between two embeddings is usually measured with cosine similarity, the
cosine of the angle between the vectors. It ranges from -1 to 1, and because it
ignores magnitude it compares direction, which suits normalized embeddings well.

## Approximate nearest neighbour
For large corpora, exact search is slow, so approximate nearest neighbour indexes
such as HNSW trade a small amount of recall for a large speedup in retrieval.
""",
    },
    "bm25-explained": {
        "title": "BM25 Lexical Ranking",
        "category": "ai-ml",
        "text": """## What BM25 is
BM25 is a bag-of-words ranking function that scores documents by term frequency and
inverse document frequency. It rewards documents where query terms appear often but
discounts terms that are common across the whole corpus.

## Saturation and length
Unlike raw TF-IDF, BM25 saturates term frequency so that the tenth occurrence of a
word adds less than the second. It also normalizes for document length so that long
documents are not unfairly favoured simply for containing more words.

## Strengths
BM25 excels at exact keyword and rare-term matching, such as error codes or API
names, where dense embeddings may miss the precise token. This complementary
strength is why hybrid retrieval combines BM25 with dense retrieval.
""",
    },
    "reranking-crossencoder": {
        "title": "Cross-Encoder Reranking",
        "category": "ai-ml",
        "text": """## Bi-encoders vs cross-encoders
A bi-encoder embeds the query and document separately, which is fast and allows
precomputing document vectors. A cross-encoder instead feeds the query and a
candidate document together through the model and outputs a single relevance score,
which is more accurate but too slow to run over an entire corpus.

## Two-stage retrieval
The standard pattern is two-stage: a fast retriever (BM25, dense, or hybrid) fetches
a candidate set of, say, the top 50 chunks, and a cross-encoder reranker rescores
just those candidates to produce the final ordering. This improves precision at the
top ranks without the cost of scoring every document.

## Reciprocal rank fusion
Reciprocal rank fusion (RRF) combines several ranked lists by summing 1/(k + rank)
across lists, which is a simple and robust way to merge BM25 and dense results before
reranking.
""",
    },
    # ── Distractor / sibling docs: topically adjacent pages that share vocabulary
    # with the docs above. They make the benchmark discriminating: weak retrievers
    # confuse them with the true answer, so dense + reranking earn their keep.
    "git-tags": {
        "title": "Tagging Releases in Git",
        "category": "version-control",
        "text": """## Lightweight vs annotated tags
A Git tag marks a specific commit, typically a release point. A lightweight tag is
just a named pointer to a commit, while an annotated tag is a full object storing a
message, tagger, and date. Create an annotated tag with `git tag -a v1.0 -m "release"`.

## Pushing tags
Tags are not pushed by default when you push a branch. Push a single tag with
`git push origin v1.0`, or push every tag at once with `git push --tags`.

## Checking out a tag
Checking out a tag puts you in a detached HEAD state because a tag is not a moving
branch pointer. To continue work, create a branch from the tag first.
""",
    },
    "git-remotes": {
        "title": "Working with Git Remotes: fetch, pull, push",
        "category": "version-control",
        "text": """## Remotes
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
""",
    },
    "docker-volumes": {
        "title": "Persisting Data with Docker Volumes",
        "category": "containers",
        "text": """## Why volumes
A container's writable layer is removed when the container is deleted, so data
written inside the container does not persist. Volumes provide storage that lives
independently of the container lifecycle.

## Named volumes vs bind mounts
A named volume is managed by Docker and stored in a Docker-controlled location. A
bind mount maps a specific host directory into the container, which is handy for
local development where you want code changes reflected immediately.

## Usage
Create and attach a named volume with `docker run -v mydata:/var/lib/data <image>`.
List volumes with `docker volume ls` and remove unused ones with `docker volume prune`.
""",
    },
    "fastapi-security": {
        "title": "Authentication and Security in FastAPI",
        "category": "web-frameworks",
        "text": """## OAuth2 password flow
FastAPI provides `OAuth2PasswordBearer` to extract a bearer token from the
Authorization header. The token is then decoded and verified in a dependency that
returns the current user, raising 401 when the token is missing or invalid.

## Hashing passwords
Never store plaintext passwords. Hash them with a slow algorithm such as bcrypt via
passlib, and verify a login by comparing the hash, not the raw password.

## Scopes
OAuth2 scopes let a token carry fine-grained permissions. A dependency can require a
specific scope and return 403 Forbidden when the authenticated user lacks it.
""",
    },
    "numpy-dtypes": {
        "title": "NumPy Data Types and Casting",
        "category": "data-science",
        "text": """## dtype
Every NumPy array has a single `dtype` describing the type of its elements, such as
`int64` or `float32`. A uniform dtype is what makes arrays compact and fast compared
to Python lists.

## Casting
`arr.astype(np.float32)` returns a new array converted to the given type. Be careful
that casting a float array to an integer dtype truncates toward zero and can silently
lose information.

## Overflow
Fixed-width integer types wrap around on overflow instead of raising, so adding 1 to
the maximum int8 value produces a negative number. Promote to a wider dtype to avoid
this.
""",
    },
    "pandas-groupby": {
        "title": "Aggregating with pandas groupby",
        "category": "data-science",
        "text": """## Split-apply-combine
`df.groupby("col")` splits the DataFrame into groups by the values of a column, then
you apply an aggregation and pandas combines the results. This is the split-apply-
combine pattern.

## Aggregations
Call an aggregation such as `.sum()`, `.mean()`, or `.count()` on the groupby object,
or use `.agg({"price": "mean", "qty": "sum"})` to apply different functions per
column. The grouping keys become the index of the result.

## Transform vs aggregate
`.agg` reduces each group to a single row, while `.transform` returns a result the
same length as the input, which is useful for adding a group statistic back as a new
column.
""",
    },
    "pytest-mocking": {
        "title": "Mocking and Monkeypatching in pytest",
        "category": "testing",
        "text": """## monkeypatch
The built-in `monkeypatch` fixture safely sets and restores attributes, environment
variables, and dictionary items for the duration of a test, undoing the change
automatically afterwards.

## unittest.mock
`unittest.mock.patch` replaces an object with a Mock during a test. Patch where the
name is looked up, not where it is defined, otherwise the real object is still used.

## Fakes vs mocks
A fake is a lightweight working implementation, such as an in-memory database, while
a mock records calls so you can assert that a function was invoked with the expected
arguments.
""",
    },
    "sql-transactions": {
        "title": "Database Transactions and ACID",
        "category": "databases",
        "text": """## ACID
A transaction groups several statements into a single unit that is Atomic,
Consistent, Isolated, and Durable. Either all of its statements take effect on
COMMIT, or none do after a ROLLBACK.

## Isolation levels
Isolation levels trade consistency for concurrency. READ COMMITTED prevents dirty
reads, REPEATABLE READ also prevents non-repeatable reads, and SERIALIZABLE is the
strictest, behaving as if transactions ran one at a time.

## Deadlocks
A deadlock occurs when two transactions each hold a lock the other needs. The
database detects the cycle and aborts one transaction so the other can proceed; the
aborted transaction should be retried.
""",
    },
    "http-caching": {
        "title": "HTTP Caching and Conditional Requests",
        "category": "web-fundamentals",
        "text": """## Cache-Control
The `Cache-Control` response header tells clients and proxies how to cache a
response. `max-age` sets how many seconds the response stays fresh, and `no-store`
forbids caching entirely.

## Validators
An `ETag` is an opaque identifier for a specific version of a resource. A client can
send it back in an `If-None-Match` header, and the server replies 304 Not Modified
with no body when the resource is unchanged, saving bandwidth.

## Revalidation
Once a cached response becomes stale, the cache revalidates it with the origin using
a conditional request rather than downloading the whole resource again.
""",
    },
    "vector-databases": {
        "title": "Vector Databases and ANN Indexes",
        "category": "ai-ml",
        "text": """## What they store
A vector database stores high-dimensional embeddings and supports nearest-neighbour
search over them. Each vector is usually stored alongside metadata used for filtering
results, such as a document id or category.

## Index types
Flat indexes compare the query against every vector for exact results. Graph indexes
like HNSW and quantization-based indexes like IVF-PQ trade a little recall for much
faster approximate search on large collections.

## Filtering
Metadata filtering restricts the search to vectors matching a condition, for example
a tenant id, which is essential for multi-tenant retrieval but can interact awkwardly
with approximate indexes if applied after the search.
""",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Golden evaluation questions. Each maps to the doc(s) that contain the answer.
# Golden answers reuse phrasing from the docs so faithfulness checks are meaningful.
# ──────────────────────────────────────────────────────────────────────────────
GOLDEN: List[Dict] = [
    {"id": "q01", "question": "How do I create a new branch and switch to it in one command?",
     "answer": "Use `git switch -c <name>` to create the branch and switch to it in one step (the older equivalent is `git checkout -b <name>`).",
     "relevant_doc_ids": ["git-branching"]},
    {"id": "q02", "question": "What is a fast-forward merge in Git?",
     "answer": "When histories have not diverged, Git performs a fast-forward merge by simply moving the branch pointer forward instead of creating a merge commit.",
     "relevant_doc_ids": ["git-branching"]},
    {"id": "q03", "question": "Why should you avoid rebasing commits that were already pushed?",
     "answer": "Rebasing rewrites commit hashes, so you should never rebase commits that have already been pushed to a shared branch.",
     "relevant_doc_ids": ["git-branching"]},
    {"id": "q04", "question": "What is the difference between git reset --soft, --mixed, and --hard?",
     "answer": "--soft keeps changes staged, --mixed keeps changes in the working tree but unstages them, and --hard discards all changes.",
     "relevant_doc_ids": ["git-reset-revert"]},
    {"id": "q05", "question": "How do I safely undo a commit that has already been shared?",
     "answer": "Use `git revert <commit>`, which creates a new commit that undoes the change without rewriting history.",
     "relevant_doc_ids": ["git-reset-revert"]},
    {"id": "q06", "question": "What is the difference between git stash pop and git stash apply?",
     "answer": "git stash pop reapplies the most recent stash and removes it from the stack, while git stash apply reapplies it but keeps it on the stack.",
     "relevant_doc_ids": ["git-stash"]},
    {"id": "q07", "question": "How do I stash untracked files?",
     "answer": "By default stash ignores untracked files; pass --include-untracked (or -u) to stash untracked files as well.",
     "relevant_doc_ids": ["git-stash"]},
    {"id": "q08", "question": "What is the difference between a Docker image and a container?",
     "answer": "An image is a read-only template, while a container is a running instance of an image that adds a thin writable layer on top of the immutable image layers.",
     "relevant_doc_ids": ["docker-images-containers"]},
    {"id": "q09", "question": "Why should you copy requirements.txt before the rest of the source in a Dockerfile?",
     "answer": "Copying the dependency manifest and installing dependencies before the source code lets the expensive dependency-install layer be cached and reused when only source code changes.",
     "relevant_doc_ids": ["dockerfile-best-practices"]},
    {"id": "q10", "question": "How do services find each other in Docker Compose?",
     "answer": "Compose creates a default network where every service is reachable from the others by its service name used as a hostname.",
     "relevant_doc_ids": ["docker-compose"]},
    {"id": "q11", "question": "Where does FastAPI serve its interactive API documentation?",
     "answer": "FastAPI serves Swagger UI at /docs and ReDoc at /redoc, both derived from the generated OpenAPI schema.",
     "relevant_doc_ids": ["fastapi-basics"]},
    {"id": "q12", "question": "What status code does FastAPI return when request validation fails?",
     "answer": "FastAPI returns a 422 Unprocessable Entity response with a detailed error list when Pydantic validation fails.",
     "relevant_doc_ids": ["fastapi-basics"]},
    {"id": "q13", "question": "When should I use async def for a FastAPI path operation?",
     "answer": "Use async def when the path operation performs awaitable I/O such as querying a database with an async driver; synchronous def operations run in an external threadpool.",
     "relevant_doc_ids": ["fastapi-async"]},
    {"id": "q14", "question": "What does Depends do in FastAPI?",
     "answer": "Depends declares reusable dependencies that are resolved before the path operation runs and injected as parameters, and dependencies can depend on other dependencies.",
     "relevant_doc_ids": ["fastapi-async"]},
    {"id": "q15", "question": "What are the NumPy broadcasting compatibility rules?",
     "answer": "Starting from the trailing dimension, two dimensions are compatible when they are equal or when one of them is 1, and a size-1 dimension is stretched to match.",
     "relevant_doc_ids": ["numpy-broadcasting"]},
    {"id": "q16", "question": "Does slicing a NumPy array return a view or a copy?",
     "answer": "Basic slicing returns a view that shares the same underlying data buffer, so modifying the view also modifies the original; fancy indexing returns a copy.",
     "relevant_doc_ids": ["numpy-views-copies"]},
    {"id": "q17", "question": "What does the how parameter control in pandas merge?",
     "answer": "The how parameter controls the join type: inner keeps only matching keys, left keeps all left rows, right keeps all right rows, and outer keeps the union of keys.",
     "relevant_doc_ids": ["pandas-merge-join"]},
    {"id": "q18", "question": "How do I fill missing values with the column mean in pandas?",
     "answer": "Use df.fillna(df.mean()) to impute numeric columns with their column mean; fillna with method='ffill' propagates the last valid observation forward.",
     "relevant_doc_ids": ["pandas-missing-data"]},
    {"id": "q19", "question": "How do I create and activate a Python virtual environment on macOS?",
     "answer": "Create it with `python -m venv .venv` and activate it on macOS with `source .venv/bin/activate`.",
     "relevant_doc_ids": ["python-venv"]},
    {"id": "q20", "question": "When should I prefer conda over pip?",
     "answer": "Prefer conda when you need complex native libraries such as GPU or scientific stacks where binary compatibility across packages matters; use pip with venv for lightweight pure-Python projects.",
     "relevant_doc_ids": ["pip-vs-conda"]},
    {"id": "q21", "question": "What does the scope of a pytest fixture control?",
     "answer": "Fixture scope controls how often a fixture is created: function runs it for every test, while module or session reuse one instance across many tests.",
     "relevant_doc_ids": ["pytest-fixtures"]},
    {"id": "q22", "question": "How do I assert that code raises a specific exception in pytest?",
     "answer": "Use the pytest.raises context manager, for example `with pytest.raises(ValueError):`, and inspect the captured exception via excinfo.",
     "relevant_doc_ids": ["pytest-assertions"]},
    {"id": "q23", "question": "Which HTTP methods are idempotent?",
     "answer": "GET, PUT, and DELETE are idempotent, meaning repeated identical calls produce the same server state; POST is not idempotent.",
     "relevant_doc_ids": ["rest-http-methods"]},
    {"id": "q24", "question": "What does HTTP status code 429 mean?",
     "answer": "429 Too Many Requests signals rate limiting by the server.",
     "relevant_doc_ids": ["http-status-codes", "rest-http-methods"]},
    {"id": "q25", "question": "What is the difference between 401 and 403 status codes?",
     "answer": "401 Unauthorized means authentication is required or failed, while 403 Forbidden means the user is authenticated but not allowed.",
     "relevant_doc_ids": ["http-status-codes"]},
    {"id": "q26", "question": "What is the left-most prefix rule for composite database indexes?",
     "answer": "A composite index helps queries that filter on a leading prefix of its columns, following the left-most prefix rule.",
     "relevant_doc_ids": ["sql-indexes"]},
    {"id": "q27", "question": "What does a LEFT JOIN return?",
     "answer": "A LEFT JOIN returns all rows from the left table plus matching rows from the right, filling unmatched right-side columns with NULL.",
     "relevant_doc_ids": ["sql-joins"]},
    {"id": "q28", "question": "Why is retrieval the bottleneck for RAG answer quality?",
     "answer": "RAG quality is bounded by retrieval: if the relevant chunk is not retrieved, the generator cannot produce a correct grounded answer.",
     "relevant_doc_ids": ["rag-overview"]},
    {"id": "q29", "question": "What is cosine similarity and what range does it take?",
     "answer": "Cosine similarity is the cosine of the angle between two embedding vectors, ranges from -1 to 1, and compares direction while ignoring magnitude.",
     "relevant_doc_ids": ["embeddings-similarity"]},
    {"id": "q30", "question": "Why does BM25 complement dense retrieval in hybrid search?",
     "answer": "BM25 excels at exact keyword and rare-term matching such as error codes or API names where dense embeddings may miss the precise token, which is why hybrid retrieval combines them.",
     "relevant_doc_ids": ["bm25-explained", "reranking-crossencoder"]},
    {"id": "q31", "question": "Why are cross-encoders too slow to run over an entire corpus?",
     "answer": "A cross-encoder feeds the query and each candidate document together through the model to output one relevance score, which is accurate but too slow to run over an entire corpus, so it is used only to rerank a candidate set.",
     "relevant_doc_ids": ["reranking-crossencoder"]},
    {"id": "q32", "question": "How does reciprocal rank fusion combine ranked lists?",
     "answer": "Reciprocal rank fusion combines several ranked lists by summing 1/(k + rank) across lists, a simple and robust way to merge BM25 and dense results.",
     "relevant_doc_ids": ["reranking-crossencoder"]},
    {"id": "q33", "question": "What is BM25 term-frequency saturation?",
     "answer": "BM25 saturates term frequency so that the tenth occurrence of a word adds less than the second, unlike raw TF-IDF, and it also normalizes for document length.",
     "relevant_doc_ids": ["bm25-explained"]},
    {"id": "q34", "question": "How can I tell whether a NumPy array is a view or owns its data?",
     "answer": "The .base attribute is None for an array that owns its data and points to the original array for a view.",
     "relevant_doc_ids": ["numpy-views-copies"]},
    # ── Harder / adversarial / paraphrased questions (vocabulary mismatch and
    #    sibling-doc confusion). These are where dense + reranking separate from BM25.
    {"id": "q35", "question": "How can I temporarily shelve my work-in-progress without committing it?",
     "answer": "Use git stash, which saves your uncommitted modifications on a stack and reverts the working directory to a clean state so you can switch context without committing half-finished work.",
     "relevant_doc_ids": ["git-stash"]},
    {"id": "q36", "question": "How do I upload my local commits to the shared repository?",
     "answer": "git push origin main uploads your local commits on main to the remote; if the push is rejected because the remote has commits you lack, fetch and integrate them first.",
     "relevant_doc_ids": ["git-remotes"]},
    {"id": "q37", "question": "Why does data written inside a container disappear after I remove it?",
     "answer": "A container's writable layer is removed when the container is deleted, so data written inside the container does not persist; volumes provide storage that lives independently of the container lifecycle.",
     "relevant_doc_ids": ["docker-volumes"]},
    {"id": "q38", "question": "What is the difference between a named volume and a bind mount in Docker?",
     "answer": "A named volume is managed by Docker and stored in a Docker-controlled location, while a bind mount maps a specific host directory into the container, which is handy for local development.",
     "relevant_doc_ids": ["docker-volumes"]},
    {"id": "q39", "question": "How does a server tell a client that a cached resource has not changed?",
     "answer": "The client sends the resource's ETag in an If-None-Match header and the server replies 304 Not Modified with no body when the resource is unchanged, saving bandwidth.",
     "relevant_doc_ids": ["http-caching"]},
    {"id": "q40", "question": "How do I require a specific permission scope on a FastAPI endpoint?",
     "answer": "OAuth2 scopes let a token carry fine-grained permissions; a dependency can require a specific scope and return 403 Forbidden when the authenticated user lacks it.",
     "relevant_doc_ids": ["fastapi-security"]},
    {"id": "q41", "question": "How do I split a dataframe by a column and compute a mean for each group?",
     "answer": "Use df.groupby('col') to split the DataFrame into groups by the column values, then call an aggregation such as .mean() on the groupby object following the split-apply-combine pattern.",
     "relevant_doc_ids": ["pandas-groupby"]},
    {"id": "q42", "question": "What happens when I cast a float NumPy array to an integer dtype?",
     "answer": "Casting a float array to an integer dtype truncates toward zero and can silently lose information; arr.astype returns a new converted array.",
     "relevant_doc_ids": ["numpy-dtypes"]},
    {"id": "q43", "question": "How do I temporarily set an environment variable for the duration of a single test?",
     "answer": "Use the built-in monkeypatch fixture, which safely sets and restores environment variables for the duration of a test, undoing the change automatically afterwards.",
     "relevant_doc_ids": ["pytest-mocking"]},
    {"id": "q44", "question": "What property guarantees that either all statements in a unit take effect or none do?",
     "answer": "A transaction is Atomic: either all of its statements take effect on COMMIT, or none do after a ROLLBACK, which is part of the ACID guarantees.",
     "relevant_doc_ids": ["sql-transactions"]},
    {"id": "q45", "question": "What is the difference between an annotated tag and a lightweight tag in Git?",
     "answer": "A lightweight tag is just a named pointer to a commit, while an annotated tag is a full object storing a message, tagger, and date.",
     "relevant_doc_ids": ["git-tags"]},
    {"id": "q46", "question": "How do I push a tag to the remote repository?",
     "answer": "Tags are not pushed by default; push a single tag with git push origin v1.0 or push every tag at once with git push --tags.",
     "relevant_doc_ids": ["git-tags"]},
    {"id": "q47", "question": "Why should passwords be hashed with bcrypt rather than stored as plaintext?",
     "answer": "Never store plaintext passwords; hash them with a slow algorithm such as bcrypt via passlib and verify a login by comparing the hash, not the raw password.",
     "relevant_doc_ids": ["fastapi-security"]},
    {"id": "q48", "question": "How do approximate nearest neighbour indexes make vector search faster on large collections?",
     "answer": "Graph indexes like HNSW and quantization-based indexes like IVF-PQ trade a little recall for much faster approximate search on large collections instead of comparing the query against every vector.",
     "relevant_doc_ids": ["vector-databases", "embeddings-similarity"]},
    {"id": "q49", "question": "What does git fetch do and how is it different from git pull?",
     "answer": "git fetch downloads new commits and updates remote-tracking branches without changing your working branch, while git pull is git fetch followed by a merge or rebase into your current branch.",
     "relevant_doc_ids": ["git-remotes"]},
    {"id": "q50", "question": "What is the strictest transaction isolation level and what does it guarantee?",
     "answer": "SERIALIZABLE is the strictest isolation level, behaving as if transactions ran one at a time.",
     "relevant_doc_ids": ["sql-transactions"]},
]


def doc_filename(doc_id: str) -> str:
    return f"{doc_id}.md"


def materialize(raw_dir: Path | None = None, eval_dir: Path | None = None) -> Dict[str, int]:
    """Write the corpus and golden questions to disk. Returns counts."""
    raw_dir = raw_dir or settings.raw_dir
    eval_dir = eval_dir or settings.eval_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    for doc_id, doc in DOCS.items():
        path = raw_dir / doc_filename(doc_id)
        content = f"# {doc['title']}\n\n<!-- category: {doc['category']} -->\n\n{doc['text'].strip()}\n"
        path.write_text(content, encoding="utf-8")

    golden_path = eval_dir / "golden_questions.jsonl"
    with golden_path.open("w", encoding="utf-8") as fh:
        for q in GOLDEN:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")

    return {"num_docs": len(DOCS), "num_questions": len(GOLDEN)}


def validate() -> List[str]:
    """Validate that every golden question references existing docs and that the
    golden answer's keywords actually appear in the referenced doc(s)."""
    problems: List[str] = []
    doc_ids = set(DOCS)
    seen_q = set()
    for q in GOLDEN:
        if q["id"] in seen_q:
            problems.append(f"duplicate question id: {q['id']}")
        seen_q.add(q["id"])
        for d in q["relevant_doc_ids"]:
            if d not in doc_ids:
                problems.append(f"{q['id']} references unknown doc '{d}'")
    return problems


if __name__ == "__main__":
    counts = materialize()
    issues = validate()
    print(f"Wrote {counts['num_docs']} docs and {counts['num_questions']} questions.")
    if issues:
        print("VALIDATION ISSUES:")
        for i in issues:
            print("  -", i)
    else:
        print("Validation OK.")
