#!/usr/bin/env python3
"""
Run all test scopes sequentially with helpful defaults and Docker checks.

Scopes order:
  1) unit
  2) integration
  3) functional

Options allow passing through to scripts/test_all.py. Exits non‑zero if any scope fails.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all test scopes sequentially")
    parser.add_argument("-n", "--parallel", type=int, default=1, help="Number of parallel workers")
    parser.add_argument("--no-coverage", action="store_true")
    parser.add_argument("--keyword", "-k", help="Pytest -k expression")
    parser.add_argument("--marker", "-m", help="Pytest -m marker selector")
    parser.add_argument("--maxfail", type=int, help="Stop after N failures per scope")
    parser.add_argument("--show-stderr", action="store_true")
    parser.add_argument("--no-docker-check", action="store_true", help="Skip Docker/Compose checks")
    parser.add_argument("--auto-up", action="store_true", help="Run 'compose up -d' if services not running")
    parser.add_argument("--compose-file", default="docker-compose.yml", help="Path to docker-compose.yml")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop at first failing scope")
    parser.add_argument("--include-performance", action="store_true", help="Also run performance tests at the end")

    args = parser.parse_args()

    test_all = str(ROOT / "test_all.py")
    common = [sys.executable, test_all]
    if args.parallel and args.parallel > 1:
        common += ["-n", str(args.parallel)]
    if args.no_coverage:
        common += ["--no-coverage"]
    if args.keyword:
        common += ["-k", args.keyword]
    if args.marker:
        common += ["-m", args.marker]
    if args.maxfail:
        common += ["--maxfail", str(args.maxfail)]
    if args.show_stderr:
        common += ["--show-stderr"]
    # Compose settings
    compose_flags = []
    if args.auto_up:
        compose_flags.append("--auto-up")
    if args.compose_file:
        compose_flags += ["--compose-file", args.compose_file]

    scopes = ["unit", "integration", "functional"]
    if args.include_performance:
        scopes.append("performance")

    results: list[tuple[str, int]] = []

    for i, scope in enumerate(scopes):
        cmd = common + ["--scope", scope]
        # Only run Docker checks on first scope unless explicitly disabled
        if args.no_docker_check:
            cmd.append("--no-docker-check")
        elif i == 0:
            cmd += compose_flags
        else:
            cmd.append("--no-docker-check")

        code = run(cmd)
        results.append((scope, code))
        if code != 0 and args.stop_on_failure:
            break

    # Summary
    print("\n================ Test Scopes Summary ================")
    overall = 0
    for scope, code in results:
        status = "OK" if code == 0 else f"FAIL({code})"
        print(f" - {scope:12}: {status}")
        overall = overall or code

    return overall


if __name__ == "__main__":
    raise SystemExit(main())

