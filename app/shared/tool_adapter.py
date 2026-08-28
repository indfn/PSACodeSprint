"""Tool schema adapter — relocated to app.tools.tool_adapter (Phase 6.5).

This module is kept for backwards compatibility. Canonical location is app.tools.tool_adapter.
"""
import warnings as _warnings
_warnings.warn(
    "Import from app.tools.tool_adapter instead of app.shared.tool_adapter",
    DeprecationWarning,
    stacklevel=2,
)
from app.tools.tool_adapter import adapt_tools_for_provider, _normalise  # noqa: F401, E402
