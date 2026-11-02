#!/usr/bin/env bash
# Fails if a git-tracked file contains a credential-shaped string.
# Prints only file and line number, never the matched text.
#
# Usage: scripts/check_secrets.sh
set -uo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Patterns are built from fragments so this script does not match itself.
PATTERNS=(
    "Google API key|AIza[0-9A-Za-z_-]{35}"
    "OpenAI/Anthropic-style key|sk-[A-Za-z0-9_-]{20,}"
    "Stripe live/test key|sk_(live|test)_[A-Za-z0-9]{16,}"
    "Stripe webhook secret|whsec_[A-Za-z0-9]{16,}"
    "Private key block|-----BEGIN ([A-Z]+ )?PRIVATE KEY-----"
    "GCP service account JSON|\"type\"[[:space:]]*:[[:space:]]*\"service_account\""
    "GitHub token|gh[pousr]_[A-Za-z0-9]{36,}"
    "Slack token|xox[baprs]-[A-Za-z0-9-]{10,}"
)

# Files that legitimately contain high-entropy text (lock files hold integrity hashes).
EXCLUDES=(
    ':!scripts/check_secrets.sh'
    ':!*package-lock.json'
    ':!*.lock'
)

found=0
for entry in "${PATTERNS[@]}"; do
    label=${entry%%|*}
    regex=${entry#*|}
    # -n gives "file:line:content"; cut keeps only file and line so the match is never printed.
    hits=$(git grep -nIE -e "$regex" -- . "${EXCLUDES[@]}" 2>/dev/null | cut -d: -f1,2)
    if [ -n "$hits" ]; then
        found=1
        while IFS= read -r location; do
            echo "ERREUR [$label] $location"
        done <<< "$hits"
    fi
done

if [ "$found" -ne 0 ]; then
    echo "" >&2
    echo "Des secrets semblent versionnés. Retire-les, révoque-les, puis passe-les par Secret Manager." >&2
    exit 1
fi

echo "OK : aucun secret détecté dans les fichiers versionnés."
