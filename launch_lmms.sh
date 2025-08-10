#!/bin/bash
# Launch LMMS with BANDMATE AI and API key

# Load API key from environment - set OPENAI_API_KEY before running
# export OPENAI_API_KEY="your_api_key_here"

echo "🎵 Launching LMMS with BANDMATE AI"
echo "API Key loaded: ${OPENAI_API_KEY:0:20}..."
echo ""
echo "In the Assistant panel, try:"
echo "  • 'Make a house beat'"
echo "  • 'Set tempo to 128'"
echo "  • 'Add reverb to lead'"
echo ""

cd build
./lmms