#!/usr/bin/env bash
# ─── FraudGuard AI — Local Setup Script ──────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🛡️  FraudGuard AI — Local Setup"
echo "================================"

# ── Detect container runtime ──────────────────────────────────────────────────
if command -v docker &>/dev/null; then
  COMPOSE_CMD="docker compose"
  CONTAINER_CMD="docker"
elif command -v podman &>/dev/null; then
  CONTAINER_CMD="podman"
  if command -v podman-compose &>/dev/null; then
    COMPOSE_CMD="podman-compose"
  else
    COMPOSE_CMD=""
  fi
else
  echo "⚠️  Neither docker nor podman found."
  echo "   On Fedora: sudo dnf install -y podman podman-compose"
  echo "   Skipping Qdrant container start. Start it manually."
  CONTAINER_CMD=""
  COMPOSE_CMD=""
fi

# 1. Copy .env if not present
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "✅ Created .env from .env.example — please fill in your API keys."
else
  echo "ℹ️  .env already exists, skipping copy."
fi

# 2. Start Qdrant
echo ""
echo "🔷 Starting Qdrant vector database..."
if [ -n "$COMPOSE_CMD" ]; then
  $COMPOSE_CMD -f "$ROOT/docker-compose.yml" up qdrant -d
  echo "✅ Qdrant running at http://localhost:6333"
elif [ -n "$CONTAINER_CMD" ]; then
  $CONTAINER_CMD run -d --name qdrant \
    -p 6333:6333 -p 6334:6334 \
    -v qdrant_data:/qdrant/storage \
    qdrant/qdrant:v1.19.1 2>/dev/null || \
    $CONTAINER_CMD start qdrant 2>/dev/null || \
    echo "ℹ️  Qdrant container already running or start failed — check manually."
  echo "✅ Qdrant running at http://localhost:6333"
else
  echo "⚠️  Skipping Qdrant — no container runtime found."
fi

# 3. Backend deps (in a venv)
echo ""
echo "🐍 Installing backend dependencies..."
cd "$ROOT/backend"

if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "   Created Python virtual environment."
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✅ Backend deps installed. Activate with: source backend/venv/bin/activate"

# 4. Ingestion deps (reuse backend venv)
echo ""
echo "📄 Installing ingestion dependencies..."
cd "$ROOT/ingestion"
pip install -r requirements.txt --quiet

# 5. Ingest advisories (only if Qdrant is reachable)
echo ""
echo "📚 Ingesting advisory documents into Qdrant..."
if curl -sf http://localhost:6333/healthz &>/dev/null || curl -sf http://localhost:6333 &>/dev/null; then
  python "$ROOT/ingestion/ingest.py" --source "$ROOT/docs/advisories"
  echo "✅ Ingestion complete."
else
  echo "⚠️  Qdrant not reachable yet — run ingestion manually after Qdrant starts:"
  echo "   source backend/venv/bin/activate"
  echo "   python ingestion/ingest.py --source docs/advisories"
fi

# 6. Frontend deps
echo ""
echo "⚛️  Installing frontend dependencies..."
if command -v npm &>/dev/null; then
  cd "$ROOT/frontend"
  npm install --silent
  echo "✅ Frontend deps installed."
else
  echo "⚠️  npm not found. Install Node.js: sudo dnf install -y nodejs npm"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Fill in API keys in $ROOT/.env  (SARVAM_API_KEY + GROQ_API_KEY minimum)"
echo "  2. Start backend:"
echo "       cd $ROOT/backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "  3. Start frontend:"
echo "       cd $ROOT/frontend && npm run dev"
echo "  4. Open http://localhost:3000"
