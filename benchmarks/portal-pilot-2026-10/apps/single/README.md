# Frozen single client portal

Experimental fictional local source from the paired benchmark. These source files preserve measured app bytes; they have known defects and are not a production release. See [complete results](../../RESULTS.md). No databases, cookies or private native logs are included.

```sh
python3 server.py --host 127.0.0.1 --port 8000 --db /tmp/atelier-single.sqlite3
```

Open http://127.0.0.1:8000. A fresh database seeds three fictional accounts:

| Role | Email | Synthetic password |
| --- | --- | --- |
| Studio | studio@aethdesign.test | StudioDemo!42 |
| Harbor client | alex@harbor.test | HarborDemo!42 |
| Northline client | sam@northline.test | NorthDemo!42 |

From this app folder, replay the included original backend regression tests with `python3 -B -m unittest tests.test_api -v`. Passing sampled tests does not clear the independently reproduced issues. Use a different fresh database per app when comparing seed states.
