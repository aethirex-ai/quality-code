# Client helper map

## Product boundary
Offline fictional-client domain helpers, exercised directly from Node. Canonical
implementation: `src/hotel.mjs`, `src/fitness.mjs`, `src/landscape.mjs`.
README.md and export comments define the required public behavior.

## Runtime flow
Validated input -> pure domain calculation or encoding -> returned value.

## Ownership
Hotel: stay prices, overlap, guest badge. Fitness: enrollment, cancellation,
class ordering. Landscape: estimates and affordability. Tests: `tests/*.test.mjs`.

## Contracts and state
No persistence. Public export names and schemas remain stable. Money uses integer
cents; dates use UTC calendar nights; cancellation uses epoch milliseconds.
Inputs must not be mutated. No external systems or integrations.

## Security, privacy, and safety
Guest text is untrusted HTML content in a single-quoted attribute and text node.
All five special characters must be encoded. No secrets, real clients, auth,
privileges, or production systems exist in this isolated exercise.

## Change invariants
Observe README contracts and add focused regression evidence for behavioral fixes.
Keep source, contracts, and tests coherent. Scope is normal contained behavior.

## Verification
Quality profiles execute local Node tests and syntax checks. Existing controls
are intentionally partial; reviewer-supplied regressions cover discovered defects.

## Do not edit casually
Public contracts, stable input order, integer boundaries, and HTML encoding.

## Context routing
`.quality/quality.toml` routes all fixture files to normal risk and real tests.
