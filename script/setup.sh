#!/bin/bash

# =============================================================================
# Chatbot AI Research Assistant - Full Setup Script
# =============================================================================
# This script sets up EVERYTHING for a fresh machine:
# 1. Check system requirements (conda, node)
# 2. Create conda environment
# 3. Install backend dependencies
# 4. Install frontend dependencies
# 5. Create .env template files
# 6. Print next steps
# =============================================================================

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
CONDA_ENV="chatbot-sinno"
PYTHON_VERSION="3.11"
NODE_MIN_VERSION=18

echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║     🚀 AI Research Assistant - Full Setup Wizard 🚀        ║${NC}"
echo -e "${MAGENTA}║     Powered by LangGraph + Next.js + MegaLLM               ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}\n"

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${CYAN}📍 Project Root: $PROJECT_ROOT${NC}\n"

# ===========================================
# Step 1: System Requirements Check
# ===========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Step 1: Checking System Requirements${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

REQUIREMENTS_MET=true

# Check conda
echo -e "${CYAN}Checking Conda...${NC}"
if command -v conda &> /dev/null; then
    echo -e "${GREEN}  ✅ Conda: $(conda --version)${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
else
    echo -e "${RED}  ❌ Conda not found${NC}"
    echo -e "${YELLOW}     Install: brew install --cask miniconda (macOS)${NC}"
    echo -e "${YELLOW}     Or: https://docs.conda.io/en/latest/miniconda.html${NC}"
    REQUIREMENTS_MET=false
fi

# Check node
echo -e "${CYAN}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -ge "$NODE_MIN_VERSION" ]; then
        echo -e "${GREEN}  ✅ Node.js: $(node -v)${NC}"
    else
        echo -e "${RED}  ❌ Node.js version too old (need >= $NODE_MIN_VERSION)${NC}"
        REQUIREMENTS_MET=false
    fi
else
    echo -e "${RED}  ❌ Node.js not found${NC}"
    echo -e "${YELLOW}     Install: brew install node (macOS)${NC}"
    echo -e "${YELLOW}     Or: https://nodejs.org/${NC}"
    REQUIREMENTS_MET=false
fi

# Check npm
echo -e "${CYAN}Checking npm...${NC}"
if command -v npm &> /dev/null; then
    echo -e "${GREEN}  ✅ npm: $(npm -v)${NC}"
else
    echo -e "${RED}  ❌ npm not found${NC}"
    REQUIREMENTS_MET=false
fi

echo ""

if [ "$REQUIREMENTS_MET" = false ]; then
    echo -e "${RED}❌ Some requirements are missing. Please install them first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All system requirements met!${NC}\n"

# ===========================================
# Step 2: Setup Conda Environment
# ===========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🐍 Step 2: Setting up Conda Environment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if conda env list | grep -q "^$CONDA_ENV "; then
    echo -e "${GREEN}✅ Environment '$CONDA_ENV' already exists${NC}"
else
    echo -e "${YELLOW}🔧 Creating conda environment '$CONDA_ENV' with Python $PYTHON_VERSION...${NC}"
    conda create -n "$CONDA_ENV" python="$PYTHON_VERSION" -y
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Environment created successfully${NC}"
    else
        echo -e "${RED}❌ Failed to create conda environment${NC}"
        exit 1
    fi
fi

# Activate environment
conda activate "$CONDA_ENV"
echo -e "${GREEN}✅ Environment activated: $(python --version)${NC}\n"

# ===========================================
# Step 3: Install Backend Dependencies
# ===========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Step 3: Installing Backend Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

cd "$BACKEND_DIR"

echo -e "${YELLOW}📥 Installing Python packages from requirements.txt...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend dependencies installed${NC}\n"
else
    echo -e "${RED}❌ Failed to install backend dependencies${NC}"
    exit 1
fi

# Create required directories
mkdir -p "$BACKEND_DIR/data/faiss_index"
mkdir -p "$BACKEND_DIR/data/pdf"
mkdir -p "$BACKEND_DIR/static/images"
echo -e "${GREEN}✅ Backend directories created${NC}\n"

# ===========================================
# Step 4: Install Frontend Dependencies
# ===========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}⚛️  Step 4: Installing Frontend Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

cd "$FRONTEND_DIR"

# Determine package manager
if command -v pnpm &> /dev/null; then
    PKG_MANAGER="pnpm"
elif command -v yarn &> /dev/null; then
    PKG_MANAGER="yarn"
else
    PKG_MANAGER="npm"
fi

echo -e "${YELLOW}📥 Installing Node.js packages using $PKG_MANAGER...${NC}"
$PKG_MANAGER install

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}\n"
else
    echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
    exit 1
fi

# ===========================================
# Step 5: Create Environment Files
# ===========================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔐 Step 5: Creating Environment Files${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Backend .env
BACKEND_ENV="$BACKEND_DIR/.env"
if [ ! -f "$BACKEND_ENV" ]; then
    cat > "$BACKEND_ENV" << 'EOF'
# =============================================================================
# AI Research Assistant - Backend Environment Variables
# =============================================================================

# LLM Provider: "megallm", "openai", or "google"
LLM_PROVIDER=megallm

# MegaLLM Configuration (OpenAI-compatible API)
MEGALLM_API_KEY=your_megallm_api_key_here
MEGALLM_BASE_URL=https://api.mega.ai/v1
MEGALLM_MODEL=gpt-4o-mini

# OpenAI Configuration (alternative)
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o-mini

# Google Gemini Configuration (alternative)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_MODEL=gemini-1.5-flash

# Tavily Search API (required for web search)
TAVILY_API_KEY=your_tavily_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
    echo -e "${GREEN}✅ Created: $BACKEND_ENV${NC}"
else
    echo -e "${YELLOW}⏭️  Skipped: $BACKEND_ENV (already exists)${NC}"
fi

# Frontend .env.local
FRONTEND_ENV="$FRONTEND_DIR/.env.local"
if [ ! -f "$FRONTEND_ENV" ]; then
    cat > "$FRONTEND_ENV" << 'EOF'
# =============================================================================
# AI Research Assistant - Frontend Environment Variables
# =============================================================================

# Python Backend URL
PYTHON_BACKEND_URL=http://localhost:8000

# Next.js Configuration
NEXT_PUBLIC_APP_NAME="AI Research Assistant"
NEXT_PUBLIC_APP_VERSION="1.0.0"
EOF
    echo -e "${GREEN}✅ Created: $FRONTEND_ENV${NC}"
else
    echo -e "${YELLOW}⏭️  Skipped: $FRONTEND_ENV (already exists)${NC}"
fi

echo ""

# ===========================================
# Step 6: Summary & Next Steps
# ===========================================
echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║              🎉 Setup Complete! 🎉                         ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}✅ Conda environment: ${CYAN}$CONDA_ENV${NC}"
echo -e "${GREEN}✅ Backend dependencies: ${CYAN}installed${NC}"
echo -e "${GREEN}✅ Frontend dependencies: ${CYAN}installed${NC}"
echo -e "${GREEN}✅ Environment files: ${CYAN}created${NC}\n"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📝 NEXT STEPS:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${YELLOW}1. Configure API Keys:${NC}"
echo -e "   Edit ${CYAN}$BACKEND_ENV${NC}"
echo -e "   Add your API keys for: MegaLLM/OpenAI/Google, Tavily\n"

echo -e "${YELLOW}2. Start Backend:${NC}"
echo -e "   ${CYAN}./script/start-backend.sh${NC}\n"

echo -e "${YELLOW}3. Start Frontend (in new terminal):${NC}"
echo -e "   ${CYAN}./script/start-frontend.sh${NC}\n"

echo -e "${YELLOW}4. Or start both at once:${NC}"
echo -e "   ${CYAN}./script/start.sh${NC}\n"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌐 URLs:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "   Frontend:  ${CYAN}http://localhost:3000${NC}"
echo -e "   Backend:   ${CYAN}http://localhost:8000${NC}"
echo -e "   API Docs:  ${CYAN}http://localhost:8000/docs${NC}\n"

echo -e "${GREEN}Happy researching! 🔬${NC}\n"
