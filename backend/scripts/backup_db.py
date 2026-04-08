#!/usr/bin/env python3
"""
backup_db.py — Daily PostgreSQL backup to Backblaze B2.

What it does:
  1. Runs pg_dump against the production database
  2. Compresses the dump to a .sql.gz file
  3. Uploads to Backblaze B2 (S3-compatible)
  4. Deletes backups older than RETENTION_DAYS from B2
  5. Sends a Twilio SMS alert if any step fails

Usage:
  python3 backup_db.py

Environment variables (set in /etc/environment or the cron job):
  DATABASE_URL          — PostgreSQL connection string (same as app)
  B2_KEY_ID             — Backblaze B2 application key ID
  B2_APPLICATION_KEY    — Backblaze B2 application key (secret)
  B2_BUCKET_NAME        — Backblaze B2 bucket name (e.g. scs-db-backups)
  B2_ENDPOINT_URL       — Backblaze B2 S3 endpoint (e.g. https://s3.us-west-004.backblazeb2.com)
  BACKUP_RETENTION_DAYS — How many days of backups to keep (default: 30)
  ALERT_PHONE_NUMBER    — Phone number to SMS on failure (e.g. +13215550100)
  TWILIO_ACCOUNT_SID    — Twilio SID (for failure alerts)
  TWILIO_AUTH_TOKEN     — Twilio auth token (for failure alerts)
  TWILIO_PHONE_NUMBER   — Twilio from number (for failure alerts)
"""

import gzip
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/db_backup.log"),
    ],
)
log = logging.getLogger("backup_db")

# ── Config ─────────────────────────────────────────────────────────────────────

DATABASE_URL       = os.environ["DATABASE_URL"]
B2_KEY_ID          = os.environ["B2_KEY_ID"]
B2_APPLICATION_KEY = os.environ["B2_APPLICATION_KEY"]
B2_BUCKET_NAME     = os.environ["B2_BUCKET_NAME"]
B2_ENDPOINT_URL    = os.environ["B2_ENDPOINT_URL"]
RETENTION_DAYS     = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

ALERT_PHONE        = os.getenv("ALERT_PHONE_NUMBER")
TWILIO_SID         = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN       = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM        = os.getenv("TWILIO_PHONE_NUMBER")

BACKUP_PREFIX      = "db-backups/"   # folder inside the B2 bucket


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_db_url(url: str) -> dict:
    """Extract connection parts from a postgres:// or postgresql+psycopg2:// URL."""
    # Normalise DigitalOcean's postgres:// prefix
    url = url.replace("postgresql+psycopg2://", "postgresql://").replace("postgres://", "postgresql://")
    p = urlparse(url)
    return {
        "host":     p.hostname,
        "port":     str(p.port or 5432),
        "user":     p.username,
        "password": p.password,
        "dbname":   p.path.lstrip("/"),
    }


def _send_alert(message: str) -> None:
    """Send an SMS alert via Twilio. Silently skips if credentials are missing."""
    if not all([ALERT_PHONE, TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM]):
        log.warning("Alert SMS skipped — TWILIO credentials or ALERT_PHONE_NUMBER not set")
        return
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=message, from_=TWILIO_FROM, to=ALERT_PHONE)
        log.info("Alert SMS sent to %s", ALERT_PHONE)
    except Exception as e:
        log.error("Failed to send alert SMS: %s", e)


def _b2_client():
    """Return a boto3 S3 client pointed at Backblaze B2."""
    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT_URL,
        aws_access_key_id=B2_KEY_ID,
        aws_secret_access_key=B2_APPLICATION_KEY,
        config=Config(signature_version="s3v4"),
    )


# ── Steps ──────────────────────────────────────────────────────────────────────

def dump_database(dest_path: Path) -> None:
    """Run pg_dump and write a plain-SQL dump to dest_path."""
    conn = _parse_db_url(DATABASE_URL)
    log.info("Dumping database '%s' from %s…", conn["dbname"], conn["host"])

    env = os.environ.copy()
    env["PGPASSWORD"] = conn["password"]

    result = subprocess.run(
        [
            "pg_dump",
            "--no-password",
            "--format=plain",
            "--no-owner",
            "--no-acl",
            f"--host={conn['host']}",
            f"--port={conn['port']}",
            f"--username={conn['user']}",
            f"--dbname={conn['dbname']}",
            f"--file={dest_path}",
        ],
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed:\n{result.stderr}")

    size_mb = dest_path.stat().st_size / 1_048_576
    log.info("Dump complete — %.2f MB", size_mb)


def compress_file(src: Path, dest: Path) -> None:
    """Gzip-compress src → dest."""
    log.info("Compressing %s…", src.name)
    with open(src, "rb") as f_in, gzip.open(dest, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
    size_mb = dest.stat().st_size / 1_048_576
    log.info("Compressed to %.2f MB", size_mb)


def upload_to_b2(local_path: Path, object_key: str) -> None:
    """Upload local_path to Backblaze B2."""
    log.info("Uploading to B2: %s/%s…", B2_BUCKET_NAME, object_key)
    client = _b2_client()
    client.upload_file(
        str(local_path),
        B2_BUCKET_NAME,
        object_key,
        ExtraArgs={"StorageClass": "STANDARD"},
    )
    log.info("Upload complete")


def prune_old_backups() -> None:
    """Delete backups older than RETENTION_DAYS from B2."""
    log.info("Pruning backups older than %d days…", RETENTION_DAYS)
    client = _b2_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    paginator = client.get_paginator("list_objects_v2")
    deleted = 0

    for page in paginator.paginate(Bucket=B2_BUCKET_NAME, Prefix=BACKUP_PREFIX):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                log.info("  Deleting old backup: %s", obj["Key"])
                client.delete_object(Bucket=B2_BUCKET_NAME, Key=obj["Key"])
                deleted += 1

    log.info("Pruned %d old backup(s)", deleted)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    filename  = f"homeservices_{timestamp}.sql"
    gz_name   = f"{filename}.gz"
    object_key = f"{BACKUP_PREFIX}{gz_name}"

    errors = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        sql_path = tmp / filename
        gz_path  = tmp / gz_name

        # Step 1: dump
        try:
            dump_database(sql_path)
        except Exception as e:
            log.error("BACKUP FAILED — dump step: %s", e)
            errors.append(f"pg_dump failed: {e}")

        # Step 2: compress
        if not errors:
            try:
                compress_file(sql_path, gz_path)
                sql_path.unlink()   # free space
            except Exception as e:
                log.error("BACKUP FAILED — compress step: %s", e)
                errors.append(f"Compression failed: {e}")

        # Step 3: upload
        if not errors:
            try:
                upload_to_b2(gz_path, object_key)
            except Exception as e:
                log.error("BACKUP FAILED — upload step: %s", e)
                errors.append(f"B2 upload failed: {e}")

    # Step 4: prune old backups (non-fatal — don't abort on prune failure)
    if not errors:
        try:
            prune_old_backups()
        except Exception as e:
            log.warning("Prune step failed (non-fatal): %s", e)

    # Result
    if errors:
        summary = " | ".join(errors)
        log.error("Backup did NOT complete successfully: %s", summary)
        _send_alert(f"⚠️ SCS DB backup FAILED ({timestamp}): {summary}")
        sys.exit(1)
    else:
        log.info("✅ Backup complete: %s", object_key)


if __name__ == "__main__":
    main()
