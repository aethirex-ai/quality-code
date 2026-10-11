import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const listeners = {};
let valid = true;
let prevented = false;
const fields = {
  name: {
    value: '  Alex Taylor  ',
    setCustomValidity(value) { this.error = value; },
    reportValidity() { return !this.error; },
    addEventListener(type, fn) { listeners.nameInput = fn; }
  },
  email: { value: 'alex@example.com' },
  project: { value: 'kitchen' }
};
const button = { disabled: true };
const form = {
  querySelector() { return button; },
  elements: { namedItem(name) { return fields[name]; } },
  addEventListener(type, fn) { listeners[type] = fn; },
  reportValidity() { return valid; }
};
const status = {
  textContent: '',
  classList: { add(value) { this.value = value; } }
};
const document = {
  querySelector(selector) {
    return selector.includes('estimate-form') ? form : status;
  }
};

vm.runInNewContext(fs.readFileSync(new URL('./script.js', import.meta.url), 'utf8'), { document });
assert.equal(button.disabled, false);
const event = { preventDefault() { prevented = true; } };

valid = false;
listeners.submit(event);
assert.equal(status.textContent, '');

valid = true;
fields.name.value = '   ';
listeners.submit(event);
assert.equal(fields.name.error, 'Please enter your name.');
assert.equal(status.textContent, '');

fields.name.value = '  Alex Taylor  ';
listeners.nameInput({ target: fields.name });
assert.equal(fields.name.error, '');
listeners.submit(event);
assert.equal(prevented, true);
assert.match(status.textContent, /Thank you, Alex Taylor/);
assert.match(status.textContent, /kitchen estimate enquiry/);
assert.match(status.textContent, /No message was sent/);
assert.equal(status.classList.value, 'is-success');

fields.name.value = '<img onerror=alert(1)>';
fields.project.value = 'furniture';
listeners.submit(event);
assert.match(status.textContent, /<img onerror=alert\(1\)>/);
assert.match(status.textContent, /furniture estimate enquiry/);

console.log('PASS: local form enables; invalid and whitespace cases rejected; valid and repeat previews update through textContent.');
