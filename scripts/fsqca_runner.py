#!/usr/bin/env python3
import sys, subprocess, os

# This runner exists so CI can call `python scripts/fsqca_runner.py --test` if pytest fails.
# It simply runs pytest and returns its exit code.
cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"] + sys.argv[1:]
rc = subprocess.call(cmd, env=os.environ.copy())
sys.exit(rc)
