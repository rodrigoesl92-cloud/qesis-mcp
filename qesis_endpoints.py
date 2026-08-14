"""The only sanctioned reader of data/endpoints.json.

Every outbound MCP endpoint this repository dials is declared once, in
data/endpoints.json, and resolved through here. Nothing else may hold the
literal, and scripts/verify_endpoints.py fails the build when something does.

Why this exists rather than a string at the call site. The horizon endpoint was
written down three times: once in an untracked file at the repository root that
carried the operator instruction, and twice as `local_endpoint = "..."` inside
infrastructure_mcp.py and test_client.py. Nothing asserted the three agreed, and
the one that carried the instruction was the one no consumer read. That is the
L-089 failure family, applied to an outbound address instead of an inbound one:
a value typed beside a declaration drifts from it, and the drift is invisible
until a client connects to a process that is not there.

Resolution order is the environment variable named in the declaration, then the
declared default. The environment wins because the server prints its own URL at
startup and the port moves between runs, so pinning it in a commit would change
the port for everyone to suit one session.

G-03 and G-04. This module reads variable NAMES from the declaration and the
values from the environment. It never writes a credential, never logs one, and
never accepts one as an argument.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import NamedTuple

_ROOT = Path(__file__).resolve().parent
_DECLARATION = _ROOT / "data" / "endpoints.json"


class Endpoint(NamedTuple):
    """A resolved endpoint and the account of where the value came from.

    `source` is not decoration. G-01b requires that a reader is always told
    which plane answered, and the difference between a declared default and an
    operator override is exactly that distinction at the client end: the
    default is the working tree's guess, the override is what the terminal
    actually printed. A caller that prints the URL prints the source with it.
    """
    name: str
    url: str
    source: str
    transport: str
    plane: str


def _declaration() -> dict:
    return json.loads(_DECLARATION.read_text(encoding="utf-8"))


def resolve(name: str) -> Endpoint:
    """Resolve one declared endpoint. Raises KeyError if it is not declared.

    Refusing an undeclared name is the point. Falling back to a literal for an
    unknown key would let a new endpoint enter the system without passing the
    declaration, which is the state this module was written to end.
    """
    endpoints = _declaration()["endpoints"]
    if name not in endpoints:
        raise KeyError(
            f"endpoint {name!r} is not declared in data/endpoints.json. "
            f"Declared: {sorted(endpoints)}. Add it to the declaration rather "
            f"than writing the URL at the call site."
        )
    spec = endpoints[name]
    override = os.environ.get(spec["env"], "").strip()
    return Endpoint(
        name=name,
        url=override or spec["default"],
        source=f"environment {spec['env']}" if override else "declared default",
        transport=spec["transport"],
        plane=spec["plane"],
    )


def declared_urls() -> set[str]:
    """Every literal the declaration itself carries, for the gate to exempt."""
    return {spec["default"] for spec in _declaration()["endpoints"].values()}


def describe(name: str) -> str:
    """One line naming the endpoint, its value and which source produced it."""
    e = resolve(name)
    return f"{e.name} -> {e.url}  [{e.source}, transport {e.transport}, plane: {e.plane}]"
