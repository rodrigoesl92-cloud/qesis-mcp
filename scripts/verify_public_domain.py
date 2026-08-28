#!/usr/bin/env python3
"""The address a buyer types must reach the service, not just the alias we probe.

WHY THIS EXISTS. On 2026-08-27 every gate in this ecosystem was green and the
public endpoint was a dead end. The probe workflow asserts the platform alias,
which was healthy throughout.
The address on the business card is the apex declared in data/domains.json.
It resolved, it answered, and it answered `308 Permanent Redirect` to the www
alias beside it, which had no DNS record at all. Anyone who typed the domain reached nothing, for as long as that was true,
and the registrar's own statistics recorded 768 errors in twenty four hours
against 1377 queries.

Nothing was broken in the application. The serving plane on the alias returned
the landed commit, the attested index hash and a verified chain. What was
missing was a control over the surface a customer actually uses. A surface added
without its control is unmonitored by construction, and the alias being healthy
is exactly what made it invisible.

THE DECISION IS A PURE FUNCTION so it can be tested with no network and no
credential, and so "would this have caught it" is answerable before the fact.
`assess` takes the resolved hop chain as values. `--selftest` runs it over
fixtures, including the live defect as it actually was.

Usage:  python scripts/verify_public_domain.py --selftest
        python scripts/verify_public_domain.py            (live, needs network)
Exit:   0 every declared public address reaches the service
        1 at least one does not, and the line above names it
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.request

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
DOMAINS = ROOT / "data" / "domains.json"


def public_addresses() -> list:
    """The addresses this ecosystem publishes, read from the one declaration.

    Not retyped here. data/domains.json is the single declaration of who this
    service is, verify_domains.py fails the build on any domain literal that is
    not in it, and that gate refused the first draft of this file for exactly
    that reason. An address added to `canonical` later is covered by this
    control without anyone remembering to add it twice, which is the whole
    lesson of the surface that had no control.
    """
    d = json.loads(DOMAINS.read_text(encoding="utf-8"))
    return [f"https://{h}/health" for h in (d.get("canonical") or [])]

#: Fields /health must carry for the answer to be this service rather than a
#: platform placeholder that happens to return 200.
REQUIRED_FIELDS = ("status", "service", "vintage", "index_sha256", "chain")


def assess(address: str, hops: list) -> list:
    """Does this address reach the service? Hops are values, newest last.

    Each hop is {host, resolves, status, location}. The failure this was written
    for is the third rule: a redirect is only a redirect if something is there
    to receive it.
    """
    problems = []
    if not hops:
        return [f"{address}: no hop was recorded, which is not the same as healthy"]
    for i, hop in enumerate(hops):
        host = hop.get("host", "?")
        if not hop.get("resolves"):
            where = "the address itself" if i == 0 else "the redirect target"
            problems.append(
                f"{address}: {where} {host} does not resolve. "
                f"A redirect to a host with no DNS record is a dead end, not a redirect.")
            return problems
    last = hops[-1]
    status = last.get("status")
    if status is None:
        problems.append(f"{address}: {last.get('host')} resolved but returned no status")
        return problems
    if 300 <= int(status) < 400:
        problems.append(
            f"{address}: the chain ends on {status} to {last.get('location') or 'nowhere'}, "
            f"so it never arrives")
        return problems
    if int(status) != 200:
        problems.append(f"{address}: final status {status} from {last.get('host')}")
        return problems
    body = last.get("body") or {}
    missing = [f for f in REQUIRED_FIELDS if f not in body]
    if missing:
        problems.append(
            f"{address}: 200 from {last.get('host')} but the payload is not this "
            f"service, missing {', '.join(missing)}")
    return problems


def _resolves(host: str) -> bool:
    try:
        socket.getaddrinfo(host, None, socket.AF_INET)
        return True
    except OSError:
        return False


def walk(address: str, limit: int = 5) -> list:
    """Follow an address by hand, recording each hop, redirects included.

    urllib follows redirects silently, which is the behaviour that hides this
    defect: a client that follows a redirect into NXDOMAIN reports a name error
    and the operator reads it as a network glitch. Each hop is recorded instead.
    """
    from urllib.parse import urlsplit
    hops, url = [], address
    for _ in range(limit):
        host = urlsplit(url).hostname or ""
        hop = {"host": host, "resolves": _resolves(host), "status": None,
               "location": None, "body": None}
        if not hop["resolves"]:
            hops.append(hop)
            return hops
        req = urllib.request.Request(url, headers={"User-Agent": "qesis-public-domain-check"})
        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(req, timeout=15) as r:
                hop["status"] = r.status
                hop["location"] = r.headers.get("Location")
                if r.status == 200:
                    raw = r.read(200_000).decode("utf-8", "replace")
                    try:
                        hop["body"] = json.loads(raw)
                    except json.JSONDecodeError:
                        hop["body"] = {}
        except urllib.error.HTTPError as e:                        # noqa: PERF203
            hop["status"] = e.code
            hop["location"] = e.headers.get("Location")
        except Exception as e:                                     # noqa: BLE001
            hop["status"] = None
            hop["location"] = f"{type(e).__name__}: {e}"
        hops.append(hop)
        if hop["status"] and 300 <= hop["status"] < 400 and hop["location"]:
            url = hop["location"]
            continue
        return hops
    return hops


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def selftest() -> int:
    """One the control must accept and one it must refuse, and the refusal is
    the live defect as it stood (V-2)."""
    d = json.loads(DOMAINS.read_text(encoding="utf-8"))
    apex, serving = d["canonical"][1], d["serving"]
    alias = (d.get("retired") or ["nonexistent.invalid"])[0]
    ok_hop = [{"host": apex, "resolves": True, "status": 200, "location": None,
               "body": {f: 1 for f in REQUIRED_FIELDS}}]
    cases = [
        ("an address that resolves and serves this service passes",
         assess("a", ok_hop) == []),
        ("a redirect into a host with no DNS record is refused, the live defect",
         bool(assess("a", [
             {"host": apex, "resolves": True, "status": 308,
              "location": f"https://{alias}/health"},
             {"host": alias, "resolves": False, "status": None,
              "location": None}]))),
        ("a redirect that lands somewhere real passes",
         assess("a", [
             {"host": apex, "resolves": True, "status": 308,
              "location": f"https://{serving}/health"},
             {"host": serving, "resolves": True, "status": 200, "location": None,
              "body": {f: 1 for f in REQUIRED_FIELDS}}]) == []),
        ("an address that does not resolve at all is refused",
         bool(assess("a", [{"host": apex, "resolves": False, "status": None,
                            "location": None}]))),
        ("a 200 that is not this service is refused, not counted as up",
         bool(assess("a", [{"host": apex, "resolves": True, "status": 200,
                            "location": None, "body": {"status": "ok"}}]))),
        ("a chain that ends on a redirect never arrives",
         bool(assess("a", [{"host": apex, "resolves": True, "status": 308,
                            "location": None}]))),
        ("silence is not health",
         bool(assess("a", []))),
    ]
    ok = sum(1 for _, good in cases if good)
    for label, good in cases:
        print(f"{'PASS' if good else 'FAIL'}  public-domain: {label}")
    print(f"{ok}/{len(cases)} public-domain behaviours hold")
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--address", action="append", default=None)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    problems = []
    for address in (a.address or public_addresses()):
        hops = walk(address)
        trail = " -> ".join(
            f"{h['host']}{'' if h['resolves'] else ' (no DNS)'}"
            f"{'' if h['status'] is None else ' ' + str(h['status'])}" for h in hops)
        found = assess(address, hops)
        print(f"  {'FAIL' if found else 'PASS'}  {address}")
        print(f"        {trail}")
        for p in found:
            print(f"        x {p}")
        problems += found
    print()
    if problems:
        print("PUBLIC DOMAIN CHECK FAILED: an address this ecosystem publishes does "
              "not reach the service.", file=sys.stderr)
        return 1
    print("PUBLIC DOMAIN CHECK PASSED: every published address reaches this service.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
