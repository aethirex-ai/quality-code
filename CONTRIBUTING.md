# Contributing

Start with the [project map](MAP.md), [testing profile](TESTING.md), and [standard](docs/STANDARD.md). Open an issue describing the observable problem and a minimal reproduction before proposing a broad change.

For a contribution:

1. State acceptance criteria and classify product risk.
2. Keep changes focused and preserve existing project content.
3. Add meaningful regression coverage for changed behavior.
4. Run `./quality validate` and the profiles required by the affected paths.
5. Explain results, known gaps, and compatibility impact in the pull request.

Changes to installation, bootstrap preservation, risk routing, agent instructions, or CI require independent review under this project’s risk gate. Do not include credentials, local agent settings, generated audit packets with private paths, or customer data.

Contributors retain copyright to their contributions and submit them under the repository’s MIT license. Maintainers decide acceptance; there is no promised response time.
