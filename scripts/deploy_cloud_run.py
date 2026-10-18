#!/usr/bin/env python3
"""Deploy the Google-backed demo using the existing database; no Terraform rebuild."""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command(*args, input_text=None):
    result = subprocess.run(
        ["gcloud", *args, "--quiet"], input=input_text, text=True, capture_output=True
    )
    if result.returncode:
        message = result.stderr
        if input_text:
            message = message.replace(input_text, "[redacted]")
        raise RuntimeError(message)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="aria-mira-retail")
    parser.add_argument("--region", default="asia-southeast1")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--wait-build", action="store_true", help="Wait for the build, then deploy"
    )
    parser.add_argument("--tag", default="latest")
    args = parser.parse_args()
    project, region = args.project, args.region
    common = [f"--project={project}"]
    local = ROOT / "data/local/cloud"
    local.mkdir(parents=True, exist_ok=True)
    command(
        "services",
        "enable",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "artifactregistry.googleapis.com",
        "secretmanager.googleapis.com",
        "iam.googleapis.com",
        *common,
    )
    repositories = json.loads(
        command(
            "artifacts",
            "repositories",
            "list",
            f"--location={region}",
            *common,
            "--format=json",
        )
    )
    if not any(r["name"].endswith("/arc-docker-repo") for r in repositories):
        command(
            "artifacts",
            "repositories",
            "create",
            "arc-docker-repo",
            "--repository-format=docker",
            f"--location={region}",
            *common,
        )
    accounts = json.loads(
        command("iam", "service-accounts", "list", *common, "--format=json")
    )
    for name in ("arc-backend-sa", "arc-storefront-sa"):
        if not any(a["email"].startswith(name + "@") for a in accounts):
            command("iam", "service-accounts", "create", name, *common)
    backend = f"arc-backend-sa@{project}.iam.gserviceaccount.com"
    frontend = f"arc-storefront-sa@{project}.iam.gserviceaccount.com"
    for role in (
        "roles/cloudsql.client",
        "roles/aiplatform.user",
        "roles/bigquery.jobUser",
        "roles/bigquery.dataEditor",
        "roles/logging.logWriter",
    ):
        command(
            "projects",
            "add-iam-policy-binding",
            project,
            f"--member=serviceAccount:{backend}",
            f"--role={role}",
            "--condition=None",
        )
    existing = {
        s["name"].split("/")[-1]
        for s in json.loads(command("secrets", "list", *common, "--format=json"))
    }

    def secret(name, account):
        if name not in existing:
            command(
                "secrets", "create", name, "--replication-policy=automatic", *common
            )
            command(
                "secrets",
                "versions",
                "add",
                name,
                "--data-file=-",
                *common,
                input_text=secrets.token_urlsafe(24),
            )
            existing.add(name)
        command(
            "secrets",
            "add-iam-policy-binding",
            name,
            f"--member=serviceAccount:{account}",
            "--role=roles/secretmanager.secretAccessor",
            *common,
        )
        versions = json.loads(
            command("secrets", "versions", "list", name, *common, "--format=json")
        )
        return next(
            v["name"].split("/")[-1] for v in versions if v["state"] == "ENABLED"
        )

    db_version = secret("arc-db-password", backend)
    aria_version = secret("arc-aria-demo-password", frontend)
    pulse_version = secret("arc-pulse-demo-password", backend)
    if not args.skip_build:
        print("Submitting container build...", flush=True)
        build = json.loads(
            command(
                "builds",
                "submit",
                str(ROOT),
                f"--config={ROOT / 'cloudbuild.yaml'}",
                f"--substitutions=_REGION={region},_TAG={args.tag}",
                "--async",
                *common,
                "--format=json",
            )
        )
        (local / "build.json").write_text(json.dumps(build, indent=2))
        print("BUILD_ID=" + build["id"], flush=True)
        if not args.wait_build:
            print("Run again with --skip-build after the build succeeds.", flush=True)
            return
        for _ in range(180):
            status = command(
                "builds", "describe", build["id"], *common, "--format=value(status)"
            )
            if status == "SUCCESS":
                break
            if status not in {"QUEUED", "WORKING", "PENDING"}:
                raise RuntimeError("Container build ended with status " + status)
            print("Container build: " + status, flush=True)
            time.sleep(10)
        else:
            raise RuntimeError("Timed out waiting for the container build")
    shared = {
        "USE_MOCK": "false",
        "ENVIRONMENT": "production",
        "GOOGLE_CLOUD_PROJECT": project,
        "GOOGLE_CLOUD_REGION": region,
        "VERTEX_AI_LOCATION": region,
        "CLOUD_SQL_INSTANCE": f"{project}:{region}:arc-postgres-instance",
        "ALLOYDB_DATABASE": "arc",
        "ALLOYDB_USER": "arc_admin",
        "BIGQUERY_DATASET": "arc_dataset",
        "BIGQUERY_LOCATION": region,
        "GEMINI_PRO_MODEL": "gemini-2.5-flash",
        "GEMINI_FLASH_MODEL": "gemini-2.5-flash",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIM": "768",
    }
    image = f"{region}-docker.pkg.dev/{project}/arc-docker-repo"

    def deploy(
        name,
        container,
        account,
        env,
        secret_args,
        public=False,
        concurrency="8",
        timeout="180",
    ):
        path = local / f"{name}-env.json"
        path.write_text(json.dumps(env))
        command(
            "run",
            "deploy",
            name,
            f"--image={image}/{container}:{args.tag}",
            f"--region={region}",
            f"--service-account={account}",
            "--allow-unauthenticated" if public else "--no-allow-unauthenticated",
            "--ingress=all",
            "--cpu=1",
            "--memory=1Gi",
            "--min-instances=0",
            "--max-instances=2",
            f"--concurrency={concurrency}",
            f"--timeout={timeout}",
            *(["--session-affinity"] if container == "pulse-dashboard" else []),
            f"--env-vars-file={path}",
            f"--set-secrets={secret_args}",
            *common,
        )
        url = command(
            "run",
            "services",
            "describe",
            name,
            f"--region={region}",
            *common,
            "--format=value(status.url)",
        )
        print(f"{name}: {url}", flush=True)
        return url

    aria = deploy(
        "arc-aria-agent",
        "aria-agent",
        backend,
        shared,
        f"ALLOYDB_PASSWORD=arc-db-password:{db_version}",
    )
    pulse = deploy(
        "arc-pulse-agent",
        "pulse-agent",
        backend,
        shared,
        f"ALLOYDB_PASSWORD=arc-db-password:{db_version}",
    )
    for service, account in (
        ("arc-aria-agent", frontend),
        ("arc-pulse-agent", backend),
    ):
        command(
            "run",
            "services",
            "add-iam-policy-binding",
            service,
            f"--region={region}",
            f"--member=serviceAccount:{account}",
            "--role=roles/run.invoker",
            *common,
        )
    storefront = deploy(
        "arc-storefront",
        "storefront",
        frontend,
        {
            "ARIA_AGENT_URL": aria,
            "ARIA_REQUEST_TIMEOUT_MS": "150000",
            "DEFAULT_CUSTOMER_ID": "sarah_123",
            "DEFAULT_STORE_ID": "dubai_marina_01",
            "DEMO_USERNAME": "mira-demo",
            "NODE_ENV": "production",
        },
        f"DEMO_PASSWORD=arc-aria-demo-password:{aria_version}",
        public=True,
    )
    dashboard = deploy(
        "arc-pulse-dashboard",
        "pulse-dashboard",
        backend,
        {
            **shared,
            "PULSE_AGENT_URL": pulse,
            "PULSE_REFRESH_SECONDS": "60",
            "DEMO_USERNAME": "pulse-manager",
        },
        f"ALLOYDB_PASSWORD=arc-db-password:{db_version},DEMO_PASSWORD=arc-pulse-demo-password:{pulse_version}",
        public=True,
        concurrency="20",
        timeout="3600",
    )
    urls = {
        "aria": storefront,
        "pulse": dashboard,
        "aria_agent": aria,
        "pulse_agent": pulse,
        "region": region,
        "project": project,
        "image_tag": args.tag,
    }
    (local / "deployment.json").write_text(json.dumps(urls, indent=2))
    aria_password = command(
        "secrets",
        "versions",
        "access",
        aria_version,
        "--secret=arc-aria-demo-password",
        *common,
    )
    pulse_password = command(
        "secrets",
        "versions",
        "access",
        pulse_version,
        "--secret=arc-pulse-demo-password",
        *common,
    )
    credentials = local / "ACCESS.md"
    credentials.write_text(
        f"# MIRA hosted demo access\n\nARIA: {storefront}\nUsername: mira-demo\nPassword: {aria_password}\n\nPULSE: {dashboard}\nUsername: pulse-manager\nPassword: {pulse_password}\n\nARIA: open /login and choose Sarah, Ahmed, Fatima, Kumar or Layla. All five use the ARIA password above. Usernames: mira-demo, ahmed-demo, fatima-demo, kumar-demo, layla-demo. Use the avatar menu to switch customer or sign out. PULSE uses its manager sign-in form.\n\nThese are application demo credentials, not Google or database credentials.\n"
    )
    credentials.chmod(0o600)
    print("Credentials saved to data/local/cloud/ACCESS.md (gitignored)", flush=True)


if __name__ == "__main__":
    main()
