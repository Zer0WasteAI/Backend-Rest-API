#!/usr/bin/env python3
"""
Convenience runner to execute the full test suite with sane defaults.

Wraps scripts/run_comprehensive_tests.py providing:
- Default environment for testing (FLASK_ENV=testing, TESTING=1)
- Simple flags for scope (unit/integration/functional/all)
- Pass-through for common pytest selectors (-k, -m) and parallelism
"""
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ensure_test_env():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("TESTING", "1")
    # Default JWT secret so JWT-dependent tests can run
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def detect_compose_command() -> list[str] | None:
    # Prefer `docker compose` if available
    if shutil.which("docker"):
        res = run(["docker", "compose", "version"])  # recent Docker
        if res.returncode == 0:
            return ["docker", "compose"]
    # Fallback to classic docker-compose
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return None


def check_docker_and_containers(compose_file: Path, auto_up: bool) -> None:
    # Check docker CLI
    if not shutil.which("docker") and not shutil.which("docker-compose"):
        print("[docker] Docker not found in PATH. Skipping runtime checks.")
        return

    # Check daemon availability quickly
    ps = run(["docker", "ps"]) if shutil.which("docker") else None
    if ps and ps.returncode != 0:
        print("[docker] Docker daemon not reachable. Ensure Docker Desktop/daemon is running.")
        return

    compose = detect_compose_command()
    if not compose:
        print("[docker] Neither 'docker compose' nor 'docker-compose' available. Skipping compose checks.")
        return

    if not compose_file.exists():
        print(f"[docker] Compose file not found at {compose_file}. Skipping compose checks.")
        return

    # Show current compose status
    res = run([*compose, "-f", str(compose_file), "ps"], cwd=compose_file.parent)
    print("[docker] compose ps:\n" + (res.stdout or res.stderr))

    # If auto_up requested or no running services detected, try to start
    needs_up = ("running" not in (res.stdout or "").lower())
    if auto_up or needs_up:
        print("[docker] Bringing services up (detached)...")
        up = subprocess.run([*compose, "-f", str(compose_file), "up", "-d"], cwd=compose_file.parent)
        if up.returncode != 0:
            print("[docker] Failed to start compose services. Check docker logs and try manually.")


def build_command(args) -> list:
    runner = ROOT / "scripts" / "run_comprehensive_tests.py"
    cmd = [sys.executable, str(runner)]

    # Map our simpler flags to the comprehensive runner
    if args.scope == "unit":
        cmd.extend(["--test-type", "unit"])
    elif args.scope == "integration":
        cmd.extend(["--test-type", "integration"])
    elif args.scope == "functional":
        cmd.extend(["--test-type", "functional"])
    else:
        cmd.extend(["--test-type", "all"])

    if args.no_coverage:
        cmd.append("--no-coverage")
    if args.parallel and args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    if args.marker:
        cmd.extend(["-m", args.marker])
    if args.maxfail:
        cmd.extend(["--maxfail", str(args.maxfail)])
    if args.show_stderr:
        cmd.append("--show-stderr")

    # Keep detailed failures and durations so output is helpful
    cmd.extend(["--detailed-failures", "--durations", "10", "--show-slow-tests"])

    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all tests with helpful defaults, with optional Docker checks")
    parser.add_argument("--scope", choices=["unit", "integration", "functional", "all"], default="all")
    parser.add_argument("-n", "--parallel", type=int, default=1, help="Number of parallel workers")
    parser.add_argument("--no-coverage", action="store_true")
    parser.add_argument("-k", "--keyword", help="Pytest -k expression")
    parser.add_argument("-m", "--marker", help="Pytest -m marker selector")
    parser.add_argument("--maxfail", type=int, help="Stop after N failures")
    parser.add_argument("--show-stderr", action="store_true")
    parser.add_argument("--no-docker-check", action="store_true", help="Skip Docker/Compose checks")
    parser.add_argument("--auto-up", action="store_true", help="Run 'compose up -d' if services not running")
    parser.add_argument("--compose-file", default="docker-compose.yml", help="Path to docker-compose.yml")

    args = parser.parse_args()
    ensure_test_env()
    if not args.no_docker_check:
        compose_file = (ROOT / args.compose_file).resolve()
        check_docker_and_containers(compose_file, auto_up=args.auto_up)
    cmd = build_command(args)

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
