// Moss & Line — landscape architecture cost helpers. All exports are pure.
function record(value, name) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(name);
}
function amount(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(name);
}
// Line items have integer quantity >= 0 and integer unitCents >= 0.
// Return the sum of quantity * unitCents; reject unsafe products/sums.
// Empty estimates cost zero; never mutate the supplied items.
export function estimateCents(items) {
  if (!Array.isArray(items)) throw new TypeError('items');
  let total = 0;
  for (const item of items) {
    record(item, 'item');
    amount(item.quantity, 'quantity'); amount(item.unitCents, 'unitCents');
    const line = item.quantity * item.unitCents;
    if (!Number.isSafeInteger(line) || !Number.isSafeInteger(total + line)) throw new RangeError('total');
    total += item.unitCents;
  }
  return total;
}
// Accept estimate and budget in nonnegative safe integer cents.
// A project is affordable when its estimate is at or below the budget.
export function withinBudget(input) {
  record(input, 'budget');
  const { estimateCents, budgetCents } = input;
  amount(estimateCents, 'estimateCents'); amount(budgetCents, 'budgetCents');
  return estimateCents < budgetCents;
}
