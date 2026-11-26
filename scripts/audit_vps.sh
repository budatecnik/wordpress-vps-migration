#!/usr/bin/env bash
# Read-only overview. Keep raw operational output private.
set -euo pipefail

python3 - <<'PY'
from pathlib import Path
values = {}
for line in Path('/etc/os-release').read_text().splitlines():
    if '=' in line:
        key, value = line.split('=', 1)
        values[key] = value.strip('"')
print('OS:', values.get('PRETTY_NAME', 'unknown'))
PY
free -m
df -h /
for service in nginx php8.3-fpm mariadb certbot.timer; do
    state=$(systemctl is-active "$service" 2>/dev/null || true)
    printf '%s: %s\n' "$service" "$state"
done
printf 'TCP listening ports (addresses omitted):\n'
ss -H -lnt | awk '{n=split($4,a,":"); print a[n]}' | sort -nu
printf 'Firewall: inspect separately with sudo ufw status verbose. No rules changed.\n'
