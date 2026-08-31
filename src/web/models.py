"""Compatibility alias for the former web module path."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("acc_telemetry.adapters.web.models")
