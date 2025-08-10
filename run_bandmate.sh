#!/bin/bash
# BANDMATE AI - Run Script

echo "🎵 BANDMATE AI - LMMS Launcher"
echo "================================"

# Check if Qt5 is installed
if ! brew list qt@5 &>/dev/null; then
    echo "❌ Qt5 not found. Installing..."
    brew install qt@5
else
    echo "✅ Qt5 found"
fi

# Set Qt5 path
export Qt5_DIR="/opt/homebrew/opt/qt@5"
export CMAKE_PREFIX_PATH="$Qt5_DIR"

# Check if build directory exists
if [ ! -d "build" ]; then
    echo "📁 Creating build directory..."
    mkdir -p build
fi

cd build

# Configure if needed
if [ ! -f "CMakeCache.txt" ]; then
    echo "⚙️  Configuring build..."
    cmake .. -DCMAKE_PREFIX_PATH="$Qt5_DIR" \
             -DQt5_DIR="$Qt5_DIR/lib/cmake/Qt5" \
             -DWANT_QT5=ON \
             -DCMAKE_BUILD_TYPE=Release
fi

# Build LMMS
echo "🔨 Building LMMS..."
cmake --build . --target lmms -j4

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    # Set environment for API key
    export OPENAI_API_KEY=$(grep OPENAI_API_KEY tools/beatbot/.env 2>/dev/null | cut -d'=' -f2)
    
    echo ""
    echo "🚀 Launching LMMS with BANDMATE AI..."
    echo "================================"
    echo "The Assistant panel is on the left sidebar."
    echo "Type natural language commands like:"
    echo "  • 'Make a house beat'"
    echo "  • 'Set tempo to 128'"
    echo "  • 'Add reverb to the lead'"
    echo "================================"
    echo ""
    
    # Run LMMS
    if [ -f "./lmms" ]; then
        ./lmms
    elif [ -f "./lmms.app/Contents/MacOS/lmms" ]; then
        ./lmms.app/Contents/MacOS/lmms
    else
        echo "❌ LMMS binary not found. Check build output."
        exit 1
    fi
else
    echo "❌ Build failed. Please check the errors above."
    echo ""
    echo "Common fixes:"
    echo "1. Install Qt5: brew install qt@5"
    echo "2. Install other dependencies:"
    echo "   brew install cmake fftw libsamplerate libsndfile"
    echo "3. Clean and rebuild:"
    echo "   rm -rf build && ./run_bandmate.sh"
    exit 1
fi