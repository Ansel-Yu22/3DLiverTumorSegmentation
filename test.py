"""Backward-compatible entrypoint for evaluation.

Use `python test.py` as before, or run `python -m ml.test`.
"""

import runpy


if __name__ == "__main__":
    runpy.run_module("ml.test", run_name="__main__")
