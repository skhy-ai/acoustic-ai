#!/bin/bash
# ============================================================================
# activate.sh — Virtual Environment Setup & Alias for Acoustic AI Backend
# ============================================================================
#
# USAGE:
#   source activate.sh
#
# WHAT IT DOES:
#   1. Creates a Python virtual environment (.venv) if it doesn't exist
#   2. Activates the virtual environment
#   3. Installs/upgrades all dependencies from requirements.txt
#   4. Creates a shell alias `acoustic-ai-start` to launch the backend
#   5. Prints a status summary
#
# NOTE:
#   Must be sourced (not executed) so the venv and alias persist in your shell.
# ============================================================================

set -e

# Resolve the project root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
BACKEND_DIR="$SCRIPT_DIR/sound_classifier_system"
REQ_FILE="$BACKEND_DIR/requirements.txt"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔊 Acoustic AI — Environment Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    echo "   ✓ Virtual environment created"
else
    echo "📦 Virtual environment already exists at $VENV_DIR"
fi

# Step 2: Activate
echo "🔑 Activating virtual environment ..."
source "$VENV_DIR/bin/activate"
echo "   ✓ Active: $(which python)"

# Step 3: Install dependencies
if [ -f "$REQ_FILE" ]; then
    echo "📥 Installing Python dependencies ..."
    pip install --upgrade pip -q
    pip install -r "$REQ_FILE" -q
    echo "   ✓ All dependencies installed"
else
    echo "⚠️  requirements.txt not found at $REQ_FILE"
fi

# Step 4: Create alias
alias acoustic-ai-start="cd \"$BACKEND_DIR\" && python -m api.main"
echo "🚀 Alias created: acoustic-ai-start"

# Step 5: Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Ready!"
echo ""
echo "  Start backend:   acoustic-ai-start"
echo "  API docs:        http://localhost:8000/docs"
echo "  Deactivate:      deactivate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
