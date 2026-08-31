"""Compatibility launcher for the packaged command-line adapter."""

from acc_telemetry.adapters.cli import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
