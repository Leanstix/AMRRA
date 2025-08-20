from __future__ import annotations

from typing import TypedDict


class VariableSpec(TypedDict, total=False):
    name: str
    type: str  # numeric|categorical|binary


