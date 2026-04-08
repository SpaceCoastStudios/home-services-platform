#!/usr/bin/env bash
# setup_backup_cron.sh — Install the daily DB backup cron job on the DigitalOcean droplet.
#
# Run this once on the server as root (or with sudo):
#   sudo bash setup_backup_cron.sh
#
# What it does:
#   1. Installs boto3 (required by backup_db.py)
#   2. Creates /etc/db_backup.env with your B2 + Twilio credentials
#   3. Installs a daily cron job at 2:00 AM server time
#   4. Creates the log file at /var/log/db_backup.log
#   5. Runs a test backup immediately so you can confirm it works

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_db.py"
ENV_FILE="/etc/db_backup.env"
LOG_FILE="/var/log/db_backup.log"
CRON_FILE="/etc/cron.d/db_backup"

# ── Check running as root ──────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo "❌  Please run as root: sudo bash setup_backup_cron.sh"
    exit 1
fi

echo "=== Space Coast Studios — DB Backup Setup ==="
echo ""

# ── Step 1: Install boto3 ──────────────────────────────────────────────────────
echo "▶  Installing boto3…"
pip3 install --quiet boto3
echo "✅  boto3 installed"
echo ""

# ── Step 2: Write credentials file ────────────────────────────────────────────
echo "▶  Configuring credentials…"
echo "   (You'll need your Backblaze B2 key ID, application key, bucket name,"
echo "    endpoint URL, and the phone number to alert on failure)"
echo ""

# Pull DATABASE_URL from the app's .env if it exists, otherwise prompt
APP_ENV="/root/home-services-platform/backend/.env"
if [[ -f "$APP_ENV" ]]; then
    DATABASE_URL=$(grep -E "^DATABASE_URL=" "$APP_ENV" | cut -d= -f2- | tr -d '"' || true)
    TWILIO_ACCOUNT_SID=$(grep -E "^TWILIO_ACCOUNT_SID=" "$APP_ENV" | cut -d= -f2- | tr -d '"' || true)
    TWILIO_AUTH_TOKEN=$(grep -E "^TWILIO_AUTH_TOKEN=" "$APP_ENV" | cut -d= -f2- | tr -d '"' || true)
    TWILIO_PHONE_NUMBER=$(grep -E "^TWILIO_PHONE_NUMBER=" "$APP_ENV" | cut -d= -f2- | tr -d '"' || true)
    echo "   ✅  Read DATABASE_URL and Twilio creds from $APP_ENV"
else
    read -rp "   DATABASE_URL: " DATABASE_URL
    read -rp "   TWILIO_ACCOUNT_SID: " TWILIO_ACCOUNT_SID
    read -rsp "   TWILIO_AUTH_TOKEN: " TWILIO_AUTH_TOKEN; echo
    read -rp "   TWILIO_PHONE_NUMBER (from): " TWILIO_PHONE_NUMBER
fi

read -rp "   B2_KEY_ID: " B2_KEY_ID
read -rsp "   B2_APPLICATION_KEY: " B2_APPLICATION_KEY; echo
read -rp "   B2_BUCKET_NAME (e.g. scs-db-backups): " B2_BUCKET_NAME
read -rp "   B2_ENDPOINT_URL (e.g. https://s3.us-west-004.backblazeb2.com): " B2_ENDPOINT_URL
read -rp "   ALERT_PHONE_NUMBER (your mobile, e.g. +13215550100): " ALERT_PHONE_NUMBER
echo ""

cat > "$ENV_FILE" <<EOF
DATABASE_URL=$DATABASE_URL
B2_KEY_ID=$B2_KEY_ID
B2_APPLICATION_KEY=$B2_APPLICATION_KEY
B2_BUCKET_NAME=$B2_BUCKET_NAME
B2_ENDPOINT_URL=$B2_ENDPOINT_URL
BACKUP_RETENTION_DAYS=30
ALERT_PHONE_NUMBER=$ALERT_PHONE_NUMBER
TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER
EOF

chmod 600 "$ENV_FILE"
echo "✅  Credentials written to $ENV_FILE (permissions: 600)"
echo ""

# ── Step 3: Create log file ────────────────────────────────────────────────────
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"
echo "✅  Log file ready at $LOG_FILE"
echo ""

# ── Step 4: Install cron job ───────────────────────────────────────────────────
# Runs daily at 2:00 AM server time
# Loads credentials from /etc/db_backup.env before running
cat > "$CRON_FILE" <<EOF
# Space Coast Studios — daily database backup to Backblaze B2
# Runs at 2:00 AM server time, logs to /var/log/db_backup.log
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 2 * * * root set -a; source /etc/db_backup.env; set +a; python3 $BACKUP_SCRIPT >> $LOG_FILE 2>&1
EOF

chmod 644 "$CRON_FILE"
echo "✅  Cron job installed: daily at 2:00 AM → $CRON_FILE"
echo ""

# ── Step 5: Test run ───────────────────────────────────────────────────────────
echo "▶  Running a test backup now…"
echo "   (This may take 10-30 seconds depending on database size)"
echo ""

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if python3 "$BACKUP_SCRIPT"; then
    echo ""
    echo "✅  Test backup succeeded!"
    echo "   Check your B2 bucket — you should see a file under db-backups/"
    echo "   Logs: tail -f $LOG_FILE"
else
    echo ""
    echo "❌  Test backup FAILED — check the output above and $LOG_FILE"
    echo "   Common issues:"
    echo "     - pg_dump not installed (apt install postgresql-client)"
    echo "     - Wrong DATABASE_URL"
    echo "     - Invalid B2 credentials or bucket name"
    exit 1
fi

echo ""
echo "=== Setup complete ==="
echo "   Backups run daily at 2:00 AM"
echo "   Retention: 30 days"
echo "   Location: B2 bucket '$B2_BUCKET_NAME' → db-backups/"
echo "   Failure alerts → $ALERT_PHONE_NUMBER via SMS"
echo "   Logs: $LOG_FILE"
