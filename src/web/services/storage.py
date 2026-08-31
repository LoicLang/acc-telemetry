"""Compatibility alias for the former web service module path."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("acc_telemetry.adapters.web.services.storage")
