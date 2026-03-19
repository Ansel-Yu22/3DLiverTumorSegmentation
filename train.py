"""Backward-compatible entrypoint for training.

Use `python train.py` as before, or run `python -m ml.train`.
"""

import runpy


if __name__ == "__main__":
    runpy.run_module("ml.train", run_name="__main__")
