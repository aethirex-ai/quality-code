# The Quality Code standard

A project’s quality contract should be readable by both people and coding agents. Standard version 3 combines a mandatory builder layer with an independent layer triggered by product risk.

## 1. Define the outcome

State observable acceptance criteria before implementation. Include failure behavior and compatibility when they matter. “Implement the function” is not a product outcome; “reject an expired session without changing stored state” is.

## 2. Load the right context

Read the map sections implicated by the changed files. Keep `MAP.md` within its configured word budget (900 words by default). Put generated inventories and long logs elsewhere. Update the map when ownership, contracts, or risk changes.

## 3. Classify actual product risk

Use the highest applicable risk. The default route catches every path; narrower routes can raise risk. A configured higher-risk route cannot be downgraded by the builder. Routine delivery steps inherit the underlying change’s risk; changes to deployment, signing, or rollback behavior have their own impact.

`./quality context <paths...>` reports configured routing. It cannot infer the real product impact or determine whether an agent followed the instructions.

## 4. Verify proportionately

- **Low:** one focused visual, static, or targeted confirmation.
- **Normal:** focused regression evidence and changed-scope verification.
- **High:** focused boundary and failure tests plus full verification.
- **Critical:** full and release verification plus applicable security, migration, recovery, integration, and platform evidence.

Commands are argument arrays, not shell strings. This avoids implicit shell evaluation in the runner; it does not make an arbitrary configured executable safe. Keep verification local and non-destructive. The runner stops at the first failing command.

For defects, demonstrate that the regression test detects the faulty behavior. Do not accept a flaky test by rerunning until green. Automated coverage is evidence, not a universal quality score.

## 5. Gate higher-risk work independently

Finish builder verification, then generate an audit packet with acceptance criteria and a clear Git base. The packet routes the auditor to the changed files, map sections, tests, and required profiles. Read untracked files explicitly: a Git diff does not include their contents.

A fresh auditor treats builder conclusions as untrusted, reproduces checks, remains read-only, and continues the full in-scope audit after the first finding. Use [the audit protocol](../references/AUDIT_PROTOCOL.md) and [testing reference](../references/TESTING.md).

The audit result follows [the JSON schema](../assets/project/.quality/audit-result.schema.json):

| Verdict | Meaning |
| --- | --- |
| `PASS` | Required evidence supports acceptance; residual risk is stated |
| `FAIL` | A reproducible defect, unmet criterion, missing required test, or policy violation exists |
| `BLOCKED` | Missing evidence or environment prevents a reliable verdict |

## 6. Preserve trust boundaries

Adoption preserves existing project text and refuses unmanaged wrapper and pre-existing runtime/schema/license collisions before project writes. Global installation modifies agent instruction files and copies an audit skill; review those changes before using it. Preserve secrets, customer data, local caches, and unrelated work outside public commits.

## 7. Delegate efficiently

Use [the delegation policy](DELEGATION.md) when independent implementation or investigation tasks justify helpers. Assess task difficulty separately from product risk. Use native runtime discovery and capability metadata to choose an accessible model and supported effort controls; this standard prescribes no provider or model identifiers.

Optimize expected total completion cost, including coordination, retries, and rework. Give helpers bounded scope and concise context, avoid competing file ownership, and keep the primary agent responsible for integration and validation. Required audits retain their independence and evidence requirements.

## Scope and limitations

This is an engineering workflow, not a certification or a security boundary. Instructions rely on agent cooperation. Path routes need maintenance; bootstrap detection cannot judge test quality. The CLI does not launch auditors, validate final verdict files, or enforce a merge gate. Configure your own repository protections and human review where needed.
