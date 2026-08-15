#!/usr/bin/env bash
# Download icons LOCALLY with a browser UA (D2's fetch UA gets 403'd by Wikimedia & some CDNs).
# Usage:
#   ./fetch-icons.sh kubernetes opentelemetry dynatrace          # SimpleIcons slugs -> icons/<slug>.svg
#   ./fetch-icons.sh azure=https://upload.wikimedia.org/.../Microsoft_Azure.svg   # name=URL for non-SimpleIcons
# Then reference in D2 as:  icon: icons/<name>.svg
set -euo pipefail
mkdir -p icons
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
for arg in "$@"; do
  if [[ "$arg" == *=* ]]; then name="${arg%%=*}"; url="${arg#*=}"; else name="$arg"; url="https://cdn.simpleicons.org/$arg"; fi
  code=$(curl -sL -A "$UA" -w "%{http_code}" "$url" -o "icons/$name.svg")
  if [[ "$code" == "200" && -s "icons/$name.svg" ]]; then echo "ok   icons/$name.svg"; else echo "FAIL $code  $url"; rm -f "icons/$name.svg"; fi
done
