# Fictional landing-page fixture map
## Product boundary
Three static fictional business pages: shop/index.html, craftsman/index.html, restaurant/index.html. Page-owned CSS/JS/assets stay in each page directory; index.html links the three portfolio cases. No backend, orders, payments or real bookings.
## Runtime flow
Static HTML/CSS/JavaScript served with Python HTTP server. Local demo interactions only.
## Ownership
Each page directory is a separable workstream. The primary agent owns the root portfolio index and integration.
## Contracts and state
Shop bag count changes locally. Craftsman estimate and restaurant reservation are client-side demos; no network submission or persistence. Required test selectors are in BRIEF.md.
## Security, privacy, and safety
No real businesses or customer data. Do not request API keys. Native image generation only. No unrelated files or account state changes; no commits, external deployment or messages.
## Change invariants
Preserve BRIEF.md and .quality files. Local assets only; visible fictional-case attribution. Responsive and keyboard-operable.
## Verification
Read BRIEF.md. Agent should verify its HTML, local images and demo interactions. Frozen external browser evaluator grades after completion.
