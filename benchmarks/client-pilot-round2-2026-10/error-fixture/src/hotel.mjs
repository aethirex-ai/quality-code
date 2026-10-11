// Juniper House — boutique hotel helpers. All exports are pure.
function record(value, name) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(name);
}
function cents(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(name);
}
function day(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new RangeError('date');
  const parsed = Date.parse(`${value}T00:00:00Z`);
  if (!Number.isFinite(parsed) || new Date(parsed).toISOString().slice(0, 10) !== value) throw new RangeError('date');
  return parsed;
}
function interval(start, end) {
  const a = day(start), b = day(end);
  if (b <= a) throw new RangeError('stay');
  return [a, b];
}
// ISO calendar dates; checkout is exclusive. Discount is integer 0..100.
// Return total integer cents, rounding the discounted total half upward once.
// Reject subtotals whose multiplication by 100 is not a safe integer.
export function quoteStay(input) {
  record(input, 'stay');
  const { checkIn, checkOut, nightlyCents, discountPercent = 0 } = input;
  const [start, end] = interval(checkIn, checkOut);
  cents(nightlyCents, 'nightlyCents');
  if (!Number.isInteger(discountPercent) || discountPercent < 0 || discountPercent > 100) throw new RangeError('discount');
  const subtotal = ((end - start) / 86400000) * nightlyCents;
  if (!Number.isSafeInteger(subtotal) || !Number.isSafeInteger(subtotal * 100)) throw new RangeError('total');
  return Math.floor(subtotal * (100 - discountPercent) / 100);
}
// Both intervals are [checkIn, checkOut). Adjoining stays do not overlap.
export function staysOverlap(first, second) {
  record(first, 'first'); record(second, 'second');
  const [a, b] = interval(first.checkIn, first.checkOut);
  const [c, d] = interval(second.checkIn, second.checkOut);
  return a <= d && c <= b;
}
// Return exact HTML below. name is untrusted text used in a single-quoted
// data-guest attribute AND text content. Encode &, <, >, double and single quotes.
export function guestBadge(name) {
  if (typeof name !== 'string') throw new TypeError('name');
  const safe = name.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
  return `<span data-guest='${safe}'>${safe}</span>`;
}
