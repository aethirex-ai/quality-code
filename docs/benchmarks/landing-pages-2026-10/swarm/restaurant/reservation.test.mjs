import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const script = await readFile(new URL('./script.js', import.meta.url), 'utf8');
let submit;
let valid = false;
let reportCount = 0;
let statusText = 'Choose a date and party size to request a table in this demo.';
let fetchCount = 0;
const values = new Map([
  ['name', '<img src=x onerror=alert(1)>'],
  ['email', 'guest@example.test'],
  ['date', '2026-10-12'],
  ['guests', '2'],
]);
const form = {
  addEventListener(type, callback) {
    assert.equal(type, 'submit');
    submit = callback;
  },
  checkValidity: () => valid,
  reportValidity: () => { reportCount += 1; },
};
const status = {
  set textContent(value) { statusText = value; },
  get textContent() { return statusText; },
};

class TestFormData {
  get(key) { return values.get(key); }
}

vm.runInNewContext(script, {
  document: {
    querySelector(selector) {
      if (selector === '[data-testid="reservation-form"]') return form;
      if (selector === '[data-testid="reservation-status"]') return status;
      return null;
    },
  },
  FormData: TestFormData,
  fetch: () => { fetchCount += 1; throw new Error('unexpected network request'); },
  Intl,
  Date,
});

assert.equal(typeof submit, 'function', 'the form should receive a submit handler');
let prevented = false;
submit({ preventDefault() { prevented = true; } });
assert.equal(prevented, true, 'submission should remain local');
assert.equal(reportCount, 1, 'invalid fields should be reported to the browser');
assert.match(statusText, /^Choose a date/, 'invalid submission should not show confirmation');

valid = true;
prevented = false;
submit({ preventDefault() { prevented = true; } });
assert.equal(prevented, true);
assert.match(statusText, /<img src=x onerror=alert\(1\)>/, 'the confirmation should include the submitted name as text');
assert.match(statusText, /2 guests on Monday, 12 October 2026/, 'the confirmation should include the party size and calendar date');
assert.match(statusText, /no reservation has been made/i, 'the confirmation should explain this is a demo');
assert.equal(fetchCount, 0, 'the interaction should not make network requests');
assert.equal(reportCount, 1, 'valid submission should not trigger another validity report');

console.log('Reservation demo checks passed.');
