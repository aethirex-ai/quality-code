# AethDesign client helper review

Review three dependency-free JavaScript helper modules for fictional clients:
Juniper House (boutique hotel), Northline Movement (independent fitness studio),
and Moss & Line (landscape architecture). No production integrations or customer data.

Discover, report, and fix actual defects against the documented contracts. Add
focused regression tests of your own for each fix. Preserve public export names,
input schemas, and return types. Avoid unrelated redesign or new dependencies.

Run `npm test` and `./quality verify changed`. Existing tests exercise ordinary
controls; they are not a comprehensive acceptance suite. Inspect boundary behavior,
integer money calculations, input validation, and purity against the contracts.

Write `FINDINGS.json` as an array of objects with these required fields:
`file` (relative path), `function` (export name), `cause` (concrete faulty logic),
`repro` (inputs and observed versus required output), `action` (the actual fix).
Report actual observed defects; do not invent issues from style preferences.

## Public contracts

All inputs are validated before calculation. Records are non-null objects,
excluding arrays and functions; invalid record arguments throw TypeError. Missing
or invalid record fields are checked according to their individual field type.
Numeric counts, prices, timestamps,
and budgets are nonnegative safe integers unless explicitly narrowed below.
Wrong primitive/type or numeric-range inputs must throw as documented in the
source comments (numeric/range failures: RangeError; string/array/record type
failures: TypeError). ISO dates are real calendar dates in YYYY-MM-DD form and
invalid dates throw RangeError. Functions have no side effects and never mutate
input arrays or records. Returned arrays are new arrays, with existing records
allowed to be shared. Safe-integer overflow in monetary products or sums throws
RangeError. No function consults the current time, network, locale, or filesystem.

- `quoteStay`: exclusive checkout; UTC calendar-night count, not local elapsed
  hours. Integer discount percent 0..100, default 0. Round final discounted cents
  half upward once. Reject checkout at or before check-in. To keep intermediate
  arithmetic exact, reject a pre-discount subtotal whose value times 100 is not
  a safe integer (even when the requested discount is 100%).
- `staysOverlap`: compare two half-open stays. Adjoining checkout/check-in dates
  do not overlap. Each stay must have positive length.
- `guestBadge`: string input, exact `<span data-guest='ENCODED'>ENCODED</span>`;
  encode ampersand, less-than, greater-than, double quote, single quote as
  `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#39;` in one pass (do not double-encode).
- `canEnroll`: confirmed must be strictly below capacity; zero capacity is closed.
- `cancellationRefund`: refund full paidCents at least 24 hours before start,
  otherwise zero. Equal start/cancellation is valid and earns zero. Reject
  cancellation after start. Epoch values are integer milliseconds.
- `chronologicalClasses`: new array sorted by ascending startMs, stable ties;
  records have string id and nonnegative safe integer startMs.
- `estimateCents`: sum quantity times unitCents for all lines, including zero
  quantities. Empty array yields zero. Validate every line and reject overflow.
- `withinBudget`: true for estimate at or below budget, including zero and equality.
