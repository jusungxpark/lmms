#!/bin/bash
# Safe setup script for API keys

echo "🔐 Setting up BANDMATE AI environment..."

# Check if .env exists
if [ -f "tools/beatbot/.env" ]; then
    echo "✅ .env file already exists"
else
    echo "Creating .env file..."
    cat > tools/beatbot/.env << 'EOF'
# Local environment variables - DO NOT COMMIT
# Add your API keys here (optional - app works without them)
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
EOF
    echo "✅ Created .env file"
fi

echo ""
echo "📝 To add your API keys:"
echo "   1. Edit tools/beatbot/.env"
echo "   2. Add your keys after the = signs"
echo "   3. Save the file"
echo ""
echo "⚠️  IMPORTANT: Never commit .env to git!"
echo ""
echo "Ready to run:"
echo "   cd tools/beatbot && python3 demo_scripts.py interactive"