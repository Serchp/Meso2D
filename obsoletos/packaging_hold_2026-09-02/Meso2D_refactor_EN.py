"""Compatibility wrapper for the converged Meso2d entrypoint."""

from Meso2d import *  # noqa: F401,F403
from Meso2d import main


if __name__ == "__main__":
    import sys

    sys.exit(main())
