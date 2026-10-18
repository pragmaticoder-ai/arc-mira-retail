#!/usr/bin/env python3
"""Provision the Cloud SQL development option for local apps; no Cloud Run deployment."""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess
from pathlib import Path


def gcloud(*args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["gcloud", *args, "--quiet"], input=input_text, text=True, capture_output=True
    )
    if result.returncode:
        # Do not echo command arguments, which can include a generated password.
        message = result.stderr
        for value in [
            input_text,
            *(a.split("=", 1)[1] for a in args if a.startswith("--password=")),
        ]:
            if value:
                message = message.replace(value, "[redacted]")
        raise RuntimeError(message)
    return result.stdout.strip()


def finish(project: str, region: str, instance: str) -> None:
    common = (f"--project={project}",)
    info = json.loads(
        gcloud("sql", "instances", "describe", instance, *common, "--format=json")
    )
    if info["state"] != "RUNNABLE":
        raise RuntimeError(
            f"Database is still {info['state']}; retry --finish after it is RUNNABLE"
        )
    secret_name = "arc-db-password"
    existing = json.loads(gcloud("secrets", "list", *common, "--format=json"))
    if any(s["name"].endswith("/" + secret_name) for s in existing):
        password = gcloud(
            "secrets",
            "versions",
            "access",
            "latest",
            f"--secret={secret_name}",
            *common,
        )
    else:
        password = secrets.token_urlsafe(30)
        gcloud(
            "secrets", "create", secret_name, "--replication-policy=automatic", *common
        )
        gcloud(
            "secrets",
            "versions",
            "add",
            secret_name,
            "--data-file=-",
            *common,
            input_text=password,
        )
    users = json.loads(
        gcloud(
            "sql", "users", "list", f"--instance={instance}", *common, "--format=json"
        )
    )
    if not any(u["name"] == "arc_admin" for u in users):
        gcloud(
            "sql",
            "users",
            "create",
            "arc_admin",
            f"--instance={instance}",
            f"--password={password}",
            *common,
        )
    databases = json.loads(
        gcloud(
            "sql",
            "databases",
            "list",
            f"--instance={instance}",
            *common,
            "--format=json",
        )
    )
    if not any(d["name"] == "arc" for d in databases):
        gcloud("sql", "databases", "create", "arc", f"--instance={instance}", *common)
    config = {
        "USE_MOCK": "false",
        "ENVIRONMENT": "development",
        "GOOGLE_CLOUD_PROJECT": project,
        "GOOGLE_CLOUD_REGION": region,
        "VERTEX_AI_LOCATION": region,
        "CLOUD_SQL_INSTANCE": info["connectionName"],
        "ALLOYDB_DATABASE": "arc",
        "ALLOYDB_USER": "arc_admin",
        "DB_PASSWORD_SECRET": secret_name,
        "BIGQUERY_DATASET": "arc_dataset",
        "BIGQUERY_LOCATION": region,
        "GEMINI_PRO_MODEL": "gemini-2.5-flash",
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIM": "768",
    }
    from dotenv import set_key

    path = Path(__file__).resolve().parents[1] / ".env"
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    for key, value in config.items():
        set_key(path, key, value)
    print(
        "Database, user and Secret Manager password ready. Wrote .env with resource names only."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", default="asia-southeast1")
    parser.add_argument("--instance", default="arc-postgres-instance")
    parser.add_argument(
        "--finish",
        action="store_true",
        help="Create database/user/secret and write .env after readiness",
    )
    args = parser.parse_args()
    common = (f"--project={args.project}",)
    if args.finish:
        finish(args.project, args.region, args.instance)
        return
    subprocess.run(
        ["bash", "scripts/setup_gcp_project.sh", args.project, args.region], check=True
    )
    instances = json.loads(gcloud("sql", "instances", "list", *common, "--format=json"))
    if not any(i["name"] == args.instance for i in instances):
        print(
            "Creating development Cloud SQL instance (this can take several minutes)...",
            flush=True,
        )
        gcloud(
            "sql",
            "instances",
            "create",
            args.instance,
            *common,
            f"--region={args.region}",
            "--database-version=POSTGRES_15",
            "--tier=db-f1-micro",
            "--storage-size=10GB",
            "--storage-type=SSD",
            "--availability-type=ZONAL",
            "--edition=ENTERPRISE",
            "--async",
        )
    # Database/user creation is a separate explicit bootstrap step after readiness.
    print(
        f"Instance requested: {args.project}:{args.region}:{args.instance}", flush=True
    )


if __name__ == "__main__":
    main()
