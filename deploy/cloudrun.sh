#!/usr/bin/env bash
# Deploy the API + web app to Google Cloud Run.
#
#   ./deploy/cloudrun.sh <PROJECT_ID> [REGION]
#
# Prereqs: an authenticated gcloud account with access + billing on the project,
# Docker running, and keys filled into .env. Prints the public URL + access code.
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT="${1:?usage: ./deploy/cloudrun.sh <PROJECT_ID> [REGION]}"
REGION="${2:-us-central1}"
REPO="autoimmune"
BASE="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}"

# --- load keys from .env ---
set -a; . ./.env; set +a
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY missing in .env}"

# Secrets that protect the public deployment (generated if not already set).
PASSCODE="${APP_PASSCODE:-$(openssl rand -hex 4)}"
INTERNAL_TOKEN="${INTERNAL_TOKEN:-$(openssl rand -hex 16)}"

echo "→ project=$PROJECT region=$REGION"
gcloud config set project "$PROJECT" >/dev/null
gcloud services enable run.googleapis.com artifactregistry.googleapis.com >/dev/null
gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" 2>/dev/null || true
gcloud auth configure-docker "${REGION}-docker.pkg.dev" -q >/dev/null

# --- backend API (index is baked into the image) ---
echo "→ building + pushing API image"
docker build --platform linux/amd64 -f backend/Dockerfile -t "${BASE}/api" .
docker push "${BASE}/api"
gcloud run deploy autoimmune-api \
  --image "${BASE}/api" --region "$REGION" --allow-unauthenticated \
  --port 8000 --memory 1Gi \
  --set-env-vars "CHAT_PROVIDER=${CHAT_PROVIDER:-anthropic},ANTHROPIC_CHAT_MODEL=${ANTHROPIC_CHAT_MODEL:-claude-haiku-4-5},EMBED_PROVIDER=${EMBED_PROVIDER:-gemini},GEMINI_EMBED_MODEL=${GEMINI_EMBED_MODEL:-gemini-embedding-001},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},GEMINI_API_KEY=${GEMINI_API_KEY:-},INTERNAL_TOKEN=${INTERNAL_TOKEN}"
API_URL=$(gcloud run services describe autoimmune-api --region "$REGION" --format='value(status.url)')
echo "→ API at $API_URL"

# --- web app ---
echo "→ building + pushing web image"
docker build --platform linux/amd64 -f web/Dockerfile -t "${BASE}/web" ./web
docker push "${BASE}/web"
gcloud run deploy autoimmune-web \
  --image "${BASE}/web" --region "$REGION" --allow-unauthenticated \
  --port 3000 --memory 512Mi \
  --set-env-vars "BACKEND_URL=${API_URL},INTERNAL_TOKEN=${INTERNAL_TOKEN},APP_PASSCODE=${PASSCODE}"
WEB_URL=$(gcloud run services describe autoimmune-web --region "$REGION" --format='value(status.url)')

echo
echo "=================================================="
echo "  Live at:      $WEB_URL"
echo "  Access code:  $PASSCODE"
echo "=================================================="
