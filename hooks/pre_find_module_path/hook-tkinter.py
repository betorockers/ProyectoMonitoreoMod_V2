"""Custom pre-find hook for tkinter.

This project runs on a Windows Python installation where PyInstaller's Tcl/Tk
availability probe can incorrectly mark tkinter as unavailable during analysis.
We intentionally keep the default module search path intact so tkinter's Python
package can still be collected, while Tcl/Tk runtime files are bundled
explicitly from the spec.
"""


def pre_find_module_path(hook_api):
    # No-op on purpose: preserve the normal search path instead of letting the
    # built-in hook clear it when the Tcl/Tk probe is unreliable.
    return
