# Handling Missing Data in pandas

<!-- category: data-science -->

## Detecting
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
