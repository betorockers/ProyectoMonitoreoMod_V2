"""Configura rutas Tcl/Tk dentro del paquete congelado."""

from __future__ import annotations

import os
import sys


def _internal_root() -> str:
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    base_dir = os.path.dirname(sys.executable)
    bundled = os.path.join(base_dir, "_internal")
    return bundled if os.path.isdir(bundled) else base_dir


root = _internal_root()
tcl_dir = os.path.join(root, "_tcl_data")
tk_dir = os.path.join(root, "_tk_data")

if not os.path.isdir(tcl_dir):
    tcl_dir = os.path.join(root, "tcl", "tcl8.6")
if not os.path.isdir(tk_dir):
    tk_dir = os.path.join(root, "tcl", "tk8.6")

if os.path.isdir(tcl_dir):
    os.environ["TCL_LIBRARY"] = tcl_dir
if os.path.isdir(tk_dir):
    os.environ["TK_LIBRARY"] = tk_dir
