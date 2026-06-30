# SQL Joins Explained

<!-- category: databases -->

## INNER JOIN
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
