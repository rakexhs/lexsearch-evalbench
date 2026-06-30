# NumPy Data Types and Casting

<!-- category: data-science -->

## dtype
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
