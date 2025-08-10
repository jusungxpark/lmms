#!/bin/bash
# BANDMATE AI - Quick Start Script for Hackathon Demo
# =====================================================

echo "🎹 BANDMATE AI - HACKATHON SETUP 🎹"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "\n${BLUE}Checking dependencies...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️ ffmpeg not found (optional, but recommended)${NC}"
    echo "   Install with: brew install ffmpeg"
else
    echo -e "${GREEN}✅ ffmpeg found${NC}"
fi

# Check LMMS
if [ -f "/Applications/LMMS.app/Contents/MacOS/lmms" ]; then
    echo -e "${GREEN}✅ LMMS found${NC}"
else
    echo -e "${YELLOW}⚠️ LMMS not found at /Applications/LMMS.app${NC}"
    echo "   Please install LMMS or update config.json with correct path"
fi

# Create virtual environment
echo -e "\n${BLUE}Setting up Python environment...${NC}"
if [ ! -d ".beatbot-venv" ]; then
    python3 -m venv .beatbot-venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate venv and install deps
source .beatbot-venv/bin/activate
pip install -q requests openai
echo -e "${GREEN}✅ Python packages installed${NC}"

# Check for API keys
echo -e "\n${BLUE}Checking API keys...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ OPENAI_API_KEY not set${NC}"
    echo "   GPT-5 planning will use fallback mode"
else
    echo -e "${GREEN}✅ OpenAI API key found${NC}"
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ ELEVENLABS_API_KEY not set${NC}"
    echo "   Music generation will use synthetic fallback"
else
    echo -e "${GREEN}✅ ElevenLabs API key found${NC}"
fi

# Create necessary directories
echo -e "\n${BLUE}Creating directories...${NC}"
mkdir -p build/beatbot/{generated,demos,exports}
echo -e "${GREEN}✅ Directories created${NC}"

# Test basic functionality
echo -e "\n${BLUE}Testing basic functionality...${NC}"
PYTHONPATH=. python3 tools/beatbot/beatbot.py plan "Make a house beat" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ BeatBot is working${NC}"
else
    echo -e "${RED}❌ BeatBot test failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 Setup complete! 🎉${NC}"
echo ""
echo "Quick Start Commands:"
echo "====================="
echo ""
echo "1. Interactive Demo (recommended for judges):"
echo -e "   ${YELLOW}python3 tools/beatbot/demo_scripts.py interactive${NC}"
echo ""
echo "2. Create a viral TikTok beat:"
echo -e "   ${YELLOW}python3 tools/beatbot/beatbot.py prompt \"Create viral trap beat for TikTok\"${NC}"
echo ""
echo "3. Run all demos:"
echo -e "   ${YELLOW}python3 tools/beatbot/demo_scripts.py all${NC}"
echo ""
echo "4. Test with natural language:"
echo -e "   ${YELLOW}python3 tools/beatbot/beatbot.py prompt \"Make this more jazzy\"${NC}"
echo ""
echo "Pro Tips:"
echo "========="
echo "• Start with simple commands like 'Make a beat'"
echo "• Add elements progressively: 'Add bass', 'Make it faster'"
echo "• Export for viral: 'Export for TikTok'"
echo "• Genre morphing: 'Make it trap style', 'Now make it lo-fi'"
echo ""
echo -e "${GREEN}Ready to revolutionize music creation! 🚀${NC}"