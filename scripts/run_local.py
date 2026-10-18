#!/usr/bin/env python3
"""Run local apps against Google infrastructure; stop with Ctrl+C."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Explicit offline fixture mode for tests/demos")
    parser.add_argument("--skip-checks", action="store_true", help="Skip Google connectivity preflight")
    parser.add_argument("--pulse-api-port", type=int, default=8002)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "local")
    parser.add_argument("--web-port", type=int, default=3000)
    parser.add_argument("--aria-port", type=int, default=8001)
    parser.add_argument("--pulse-port", type=int, default=8501)
    args = parser.parse_args()
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
    if args.offline:
        args.data_dir.mkdir(parents=True, exist_ok=True)
    tsconfig = ROOT / "frontend" / "aria-app" / f".tsconfig-local-{args.web_port}.json"
    tsconfig.write_text(json.dumps({"extends": "./tsconfig.json",
        "compilerOptions": {"tsBuildInfoFile": f".next-local-{args.web_port}/tsconfig.tsbuildinfo"},
        "include": ["next-env.d.ts", "app/**/*.ts", "app/**/*.tsx", "components/**/*.tsx", "context/**/*.tsx", "lib/**/*.ts",
                    f".next-local-{args.web_port}/types/**/*.ts"], "exclude": ["node_modules"]}, indent=2))
    env = {**os.environ, "USE_MOCK": "true" if args.offline else "false", "ENVIRONMENT": "development",
           "ARIA_AGENT_URL": f"http://127.0.0.1:{args.aria_port}", "PYTHONPATH": str(ROOT),
           "ARC_NEXT_DIST_DIR": f".next-local-{args.web_port}", "ARC_TSCONFIG_PATH": tsconfig.name}
    if args.offline:
        env.update(ARC_BRIDGE_DB=str(args.data_dir.resolve() / "incidents.sqlite"),
                   ARC_STATE_DB=str(args.data_dir.resolve() / "operations.sqlite"))
    else:
        env.pop("ARC_BRIDGE_DB", None)
        env.pop("ARC_STATE_DB", None)
        if not args.skip_checks:
            subprocess.run([sys.executable, "scripts/check_google.py"], cwd=ROOT, env=env, check=True)
    commands = [([sys.executable, "-m", "uvicorn", "agents.pulse.main:app", "--host", "127.0.0.1", "--port", str(args.pulse_api_port)], ROOT),([sys.executable, "-m", "uvicorn", "agents.aria.main:app", "--host", "127.0.0.1", "--port", str(args.aria_port)], ROOT),
                ([sys.executable, "-m", "streamlit", "run", "frontend/pulse-dashboard/pulse_dashboard.py",
                  "--server.address", "127.0.0.1", "--server.port", str(args.pulse_port), "--server.headless", "true"], ROOT),
                (["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", str(args.web_port)], ROOT / "frontend" / "aria-app")]
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    if not args.offline:
        env.setdefault("PULSE_REFRESH_SECONDS", "30")
    env["PULSE_AGENT_URL"] = f"http://127.0.0.1:{args.pulse_api_port}"
    env["ARIA_REQUEST_TIMEOUT_MS"] = "120000"
    processes = []
    def stop(*_):
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        for command, cwd in commands:
            processes.append(subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True))
        print(f"Storefront http://localhost:{args.web_port} | PULSE http://localhost:{args.pulse_port} | PULSE API http://localhost:{args.pulse_api_port}", flush=True)
        while all(p.poll() is None for p in processes):
            try:
                processes[0].wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        stop()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    if any(p.returncode not in (0, -signal.SIGTERM, -signal.SIGINT, 130, 143) for p in processes):
        raise SystemExit("A local service stopped unexpectedly. Inspect its output above.")


if __name__ == "__main__":
    main()
