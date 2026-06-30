# Aggregating with pandas groupby

<!-- category: data-science -->

## Split-apply-combine
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
