"""Optional legacy iteration-parser compatibility; native accounting stays unchanged.

Call only for a condition with final metadata. Raw evidence is never normalized.
"""
import argparse
import json
from pathlib import Path
import sys
MODULE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(MODULE_ROOT))
import phase_collect


def collect(condition, sessions):
    """Preserve native result; make only optional iteration ValueError explicit."""
    original = phase_collect.legacy.iteration_summary

    def optional_iterations(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except ValueError as exc:
            return {'state': 'unparsed', 'error': str(exc), 'counts': None,
                    'raw_evidence_retained': True,
                    'independent_iteration_review': 'iteration-review.json'}

    phase_collect.legacy.iteration_summary = optional_iterations
    try:
        return phase_collect.collect(condition, sessions)
    finally:
        phase_collect.legacy.iteration_summary = original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition', choices=['single', 'adaptive'])
    parser.add_argument('--sessions-dir', required=True)
    args = parser.parse_args()
    result = collect(args.condition, args.sessions_dir)
    print(json.dumps({key: result[key] for key in
                     ('completion_state', 'tokens', 'standard_short_estimated_usd', 'flags')}))


if __name__ == '__main__':
    main()
