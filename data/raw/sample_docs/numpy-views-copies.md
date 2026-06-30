# NumPy Views vs Copies

<!-- category: data-science -->

## Views
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
