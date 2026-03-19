"""Backward-compatible entrypoint for data preprocessing.

Use `python preprocess.py` as before, or run `python -m ml.preprocess`.
"""

import runpy


if __name__ == "__main__":
    runpy.run_module("ml.preprocess", run_name="__main__")
