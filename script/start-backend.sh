#!/bin/bash

# =============================================================================
# Chatbot AI Research Assistant - Backend Setup & Start Script
# =============================================================================
# This script handles:
# 1. Conda environment creation (if not exists)
# 2. Dependencies installation
# 3. Environment variables check
# 4. FastAPI backend startup with LangGraph multi-agent system
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
BACKEND_PORT=8000

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🐍 AI Research Assistant - Backend Setup${NC}"
echo -e "${BLUE}   Powered by FastAPI + LangGraph + MegaLLM${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping backend...${NC}"
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null
    pkill -f "uvicorn app.server:app" 2>/dev/null
    echo -e "${GREEN}✅ Backend stopped${NC}"
    exit
}

trap cleanup SIGINT SIGTERM

# ===========================================
# Step 1: Check & Install Conda
# ===========================================
echo -e "${CYAN}📦 Step 1: Checking Conda installation...${NC}\n"

if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌ Conda not found!${NC}"
    echo -e "${YELLOW}Please install Miniconda or Anaconda first:${NC}"
    echo -e "${CYAN}   macOS: brew install --cask miniconda${NC}"
    echo -e "${CYAN}   Linux: wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh${NC}"
    echo -e "${CYAN}   Or visit: https://docs.conda.io/en/latest/miniconda.html${NC}"
    exit 1
fi

# Initialize conda for the current shell
source "$(conda info --base)/etc/profile.d/conda.sh"
echo -e "${GREEN}✅ Conda found: $(conda --version)${NC}\n"

# ===========================================
# Step 2: Create/Check Conda Environment
# ===========================================
echo -e "${CYAN}📦 Step 2: Setting up Conda environment '$CONDA_ENV'...${NC}\n"

if conda env list | grep -q "^$CONDA_ENV "; then
    echo -e "${GREEN}✅ Environment '$CONDA_ENV' already exists${NC}"
else
    echo -e "${YELLOW}🔧 Creating new conda environment '$CONDA_ENV' with Python $PYTHON_VERSION...${NC}"
    conda create -n "$CONDA_ENV" python="$PYTHON_VERSION" -y
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Environment created successfully${NC}"
    else
        echo -e "${RED}❌ Failed to create conda environment${NC}"
        exit 1
    fi
fi

# Activate the environment
echo -e "${CYAN}🔄 Activating environment '$CONDA_ENV'...${NC}"
conda activate "$CONDA_ENV"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to activate conda environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment activated${NC}"
echo -e "   Python: ${CYAN}$(python --version)${NC}"
echo -e "   Path: ${CYAN}$(which python)${NC}\n"

# ===========================================
# Step 3: Install Dependencies
# ===========================================
echo -e "${CYAN}📦 Step 3: Installing Python dependencies...${NC}\n"

cd "$BACKEND_DIR"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found in $BACKEND_DIR${NC}"
    exit 1
fi

# Check if dependencies need to be installed
# Compare requirements.txt hash with last installed hash
HASH_FILE="$BACKEND_DIR/.requirements.hash"
CURRENT_HASH=$(md5sum requirements.txt 2>/dev/null || md5 -q requirements.txt 2>/dev/null)

if [ -f "$HASH_FILE" ] && [ "$(cat $HASH_FILE)" = "$CURRENT_HASH" ]; then
    echo -e "${GREEN}✅ Dependencies already up to date${NC}\n"
else
    echo -e "${YELLOW}📥 Installing/updating dependencies from requirements.txt...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "$CURRENT_HASH" > "$HASH_FILE"
        echo -e "${GREEN}✅ Dependencies installed successfully${NC}\n"
    else
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    fi
fi

# ===========================================
# Step 4: Check Environment Variables
# ===========================================
echo -e "${CYAN}📦 Step 4: Checking environment variables...${NC}\n"

ENV_FILE="$BACKEND_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    # Source the .env file to check variables
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo -e "${YELLOW}Creating template .env file...${NC}"
    
    cat > "$ENV_FILE" << 'EOF'
# =============================================================================
# AI Research Assistant - Environment Variables
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

    echo -e "${GREEN}✅ Template .env file created at $ENV_FILE${NC}"
    echo -e "${RED}⚠️  Please edit $ENV_FILE and add your API keys before running again!${NC}"
    exit 1
fi

# Check required API keys
MISSING_KEYS=()

if [ -z "$TAVILY_API_KEY" ] || [ "$TAVILY_API_KEY" = "your_tavily_api_key_here" ]; then
    MISSING_KEYS+=("TAVILY_API_KEY")
fi

# Check LLM provider keys
if [ "$LLM_PROVIDER" = "megallm" ]; then
    if [ -z "$MEGALLM_API_KEY" ] || [ "$MEGALLM_API_KEY" = "your_megallm_api_key_here" ]; then
        MISSING_KEYS+=("MEGALLM_API_KEY")
    fi
elif [ "$LLM_PROVIDER" = "openai" ]; then
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
        MISSING_KEYS+=("OPENAI_API_KEY")
    fi
elif [ "$LLM_PROVIDER" = "google" ]; then
    if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ]; then
        MISSING_KEYS+=("GOOGLE_API_KEY")
    fi
fi

if [ ${#MISSING_KEYS[@]} -gt 0 ]; then
    echo -e "${RED}⚠️  Missing or invalid API keys:${NC}"
    for key in "${MISSING_KEYS[@]}"; do
        echo -e "   ${RED}• $key${NC}"
    done
    echo -e "${YELLOW}Please edit $ENV_FILE and add valid API keys${NC}"
    echo -e "${YELLOW}Continuing anyway (some features may not work)...${NC}\n"
else
    echo -e "${GREEN}✅ All required environment variables are set${NC}\n"
fi

# ===========================================
# Step 5: Create Required Directories
# ===========================================
echo -e "${CYAN}📦 Step 5: Creating required directories...${NC}\n"

mkdir -p "$BACKEND_DIR/data/faiss_index"
mkdir -p "$BACKEND_DIR/data/pdf"
mkdir -p "$BACKEND_DIR/static/images"

echo -e "${GREEN}✅ Directories created:${NC}"
echo -e "   • data/faiss_index (vector database)"
echo -e "   • data/pdf (knowledge base documents)"
echo -e "   • static/images (generated plots)\n"

# ===========================================
# Step 6: Kill Existing Processes
# ===========================================
echo -e "${CYAN}🧹 Step 6: Cleaning up existing processes on port $BACKEND_PORT...${NC}"
lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null
sleep 1
echo -e "${GREEN}✅ Cleanup complete${NC}\n"

# ===========================================
# Step 7: Start Backend Server
# ===========================================
echo -e "${MAGENTA}================================================${NC}"
echo -e "${MAGENTA}🚀 Starting AI Research Assistant Backend${NC}"
echo -e "${MAGENTA}================================================${NC}"
echo -e "   Environment: ${CYAN}$CONDA_ENV${NC}"
echo -e "   Python: ${CYAN}$(python --version)${NC}"
echo -e "   Port: ${CYAN}$BACKEND_PORT${NC}"
echo -e "   URL: ${CYAN}http://localhost:$BACKEND_PORT${NC}"
echo -e "   Docs: ${CYAN}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "${MAGENTA}================================================${NC}\n"

echo -e "${YELLOW}📝 Press Ctrl+C to stop the server${NC}\n"

# Start uvicorn with auto-reload for development
python -m uvicorn app.server:app --host 0.0.0.0 --port $BACKEND_PORT --reload
