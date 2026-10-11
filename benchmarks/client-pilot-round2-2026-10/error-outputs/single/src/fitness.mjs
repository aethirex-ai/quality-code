// Northline Movement — independent fitness studio. All exports are pure.
function record(value, name) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(name);
}
function count(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(name);
}
// A class accepts enrollment only while confirmed is strictly below capacity.
// Zero capacity is closed. Inputs are nonnegative safe integer counts.
export function canEnroll(input) {
  record(input, 'class');
  const { confirmed, capacity } = input;
  count(confirmed, 'confirmed'); count(capacity, 'capacity');
  return confirmed < capacity;
}
// Integer epoch milliseconds. A cancellation at least 24 hours before start
// earns the full paidCents refund; less than 24 hours earns zero.
// Reject cancellation after start and negative/unsafe integer inputs.
export function cancellationRefund(input) {
  record(input, 'cancellation');
  const { startMs, cancelledMs, paidCents } = input;
  count(startMs, 'startMs'); count(cancelledMs, 'cancelledMs'); count(paidCents, 'paidCents');
  if (cancelledMs > startMs) throw new RangeError('cancelledMs');
  return startMs - cancelledMs >= 86400000 ? paidCents : 0;
}
// Return a new array ordered by ascending startMs, preserving original order
// for ties. Records contain string id and nonnegative safe integer startMs.
// Never mutate input array or records; records need not be copied.
export function chronologicalClasses(classes) {
  if (!Array.isArray(classes)) throw new TypeError('classes');
  for (const item of classes) {
    record(item, 'class');
    if (typeof item.id !== 'string') throw new TypeError('class');
    count(item.startMs, 'startMs');
  }
  return [...classes].sort((a, b) => a.startMs - b.startMs);
}
