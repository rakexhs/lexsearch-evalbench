# Combining Data in pandas: merge, join, concat

<!-- category: data-science -->

## merge
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
