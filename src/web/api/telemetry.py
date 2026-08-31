"""Compatibility alias for the former web API module path."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("acc_telemetry.adapters.web.api.telemetry")
