# Database Indexes and Query Performance

<!-- category: databases -->

## What an index is
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
