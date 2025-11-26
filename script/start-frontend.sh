#!/bin/bash

# =============================================================================
# Chatbot AI Research Assistant - Frontend Setup & Start Script
# =============================================================================
# This script handles:
# 1. Node.js version check
# 2. Dependencies installation (npm install)
# 3. Environment variables check
# 4. Next.js frontend startup
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
FRONTEND_PORT=3000
NODE_MIN_VERSION=18

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}⚛️  AI Research Assistant - Frontend Setup${NC}"
echo -e "${BLUE}   Powered by Next.js 15 + React 19${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping frontend...${NC}"
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    echo -e "${GREEN}✅ Frontend stopped${NC}"
    exit
}

trap cleanup SIGINT SIGTERM

# ===========================================
# Step 1: Check Node.js Installation
# ===========================================
echo -e "${CYAN}📦 Step 1: Checking Node.js installation...${NC}\n"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found!${NC}"
    echo -e "${YELLOW}Please install Node.js first:${NC}"
    echo -e "${CYAN}   macOS: brew install node${NC}"
    echo -e "${CYAN}   Or use nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash${NC}"
    echo -e "${CYAN}   Then: nvm install 20${NC}"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt "$NODE_MIN_VERSION" ]; then
    echo -e "${RED}❌ Node.js version $NODE_VERSION is too old!${NC}"
    echo -e "${YELLOW}Please upgrade to Node.js $NODE_MIN_VERSION or higher${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js found: $(node -v)${NC}"
echo -e "${GREEN}✅ npm found: $(npm -v)${NC}\n"

# ===========================================
# Step 2: Check npm/pnpm/yarn
# ===========================================
echo -e "${CYAN}📦 Step 2: Checking package manager...${NC}\n"

# Prefer pnpm if available, fallback to npm
if command -v pnpm &> /dev/null; then
    PKG_MANAGER="pnpm"
    echo -e "${GREEN}✅ Using pnpm: $(pnpm -v)${NC}\n"
elif command -v yarn &> /dev/null; then
    PKG_MANAGER="yarn"
    echo -e "${GREEN}✅ Using yarn: $(yarn -v)${NC}\n"
else
    PKG_MANAGER="npm"
    echo -e "${GREEN}✅ Using npm: $(npm -v)${NC}\n"
fi

# ===========================================
# Step 3: Install Dependencies
# ===========================================
echo -e "${CYAN}📦 Step 3: Installing Node.js dependencies...${NC}\n"

cd "$FRONTEND_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if node_modules exists and is up to date
if [ -d "node_modules" ]; then
    # Check if package-lock.json is newer than node_modules
    if [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ] 2>/dev/null; then
        echo -e "${YELLOW}📥 Dependencies may be outdated, updating...${NC}"
        $PKG_MANAGER install
    else
        echo -e "${GREEN}✅ Dependencies already installed${NC}\n"
    fi
else
    echo -e "${YELLOW}📥 Installing dependencies for the first time...${NC}"
    $PKG_MANAGER install
    
    if [ $? -eq 0 ]; then
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

ENV_FILE="$FRONTEND_DIR/.env.local"

if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✅ .env.local file found${NC}\n"
else
    echo -e "${YELLOW}⚠️  .env.local file not found!${NC}"
    echo -e "${YELLOW}Creating template .env.local file...${NC}"
    
    cat > "$ENV_FILE" << 'EOF'
# =============================================================================
# AI Research Assistant Frontend - Environment Variables
# =============================================================================

# Python Backend URL
PYTHON_BACKEND_URL=http://localhost:8000

# Next.js Configuration
NEXT_PUBLIC_APP_NAME="AI Research Assistant"
NEXT_PUBLIC_APP_VERSION="1.0.0"
EOF

    echo -e "${GREEN}✅ Template .env.local file created${NC}\n"
fi

# ===========================================
# Step 5: Kill Existing Processes
# ===========================================
echo -e "${CYAN}🧹 Step 5: Cleaning up existing processes on port $FRONTEND_PORT...${NC}"
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null
sleep 1
echo -e "${GREEN}✅ Cleanup complete${NC}\n"

# ===========================================
# Step 6: Start Frontend Server
# ===========================================
echo -e "${MAGENTA}================================================${NC}"
echo -e "${MAGENTA}🚀 Starting AI Research Assistant Frontend${NC}"
echo -e "${MAGENTA}================================================${NC}"
echo -e "   Node.js: ${CYAN}$(node -v)${NC}"
echo -e "   Package Manager: ${CYAN}$PKG_MANAGER${NC}"
echo -e "   Port: ${CYAN}$FRONTEND_PORT${NC}"
echo -e "   URL: ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "${MAGENTA}================================================${NC}\n"

echo -e "${YELLOW}📝 Press Ctrl+C to stop the server${NC}\n"

# Start Next.js development server
$PKG_MANAGER run dev
