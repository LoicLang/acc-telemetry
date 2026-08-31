"""Compatibility alias for the pre-package module path."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("acc_telemetry.extraction.laps")
