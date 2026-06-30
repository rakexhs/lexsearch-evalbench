# NumPy Broadcasting Rules

<!-- category: data-science -->

## The rule
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
