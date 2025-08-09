# LMMS AI Assistant Sidebar

## Overview

The AI Assistant Sidebar is a revolutionary addition to LMMS that integrates GPT-5 AI capabilities directly into your music production workflow. This intelligent sidebar provides comprehensive project assistance, creative suggestions, and automated task execution using cutting-edge agentic AI principles.

## Features

### 🎯 GPT-5 Integration
- **Latest Model**: Uses GPT-5 with advanced reasoning capabilities
- **New API Features**: Leverages minimal reasoning effort, custom verbosity, and freeform tool calling
- **Context Awareness**: Maintains conversation history and reasoning context between interactions
- **Tool Preambles**: AI explains its actions before executing them for transparency

### 🛠️ Comprehensive Tool Usage
The AI assistant has access to powerful tools for complete LMMS project manipulation:

- **Project Analysis**: Read and analyze current project structure, tracks, tempo, and settings
- **Track Management**: Mute, unmute, solo, rename tracks programmatically  
- **Instrument Control**: Add new instruments and configure plugins
- **Audio Analysis**: Analyze frequency spectrum, BPM detection, key detection
- **Pattern Generation**: Generate musical patterns based on style and parameters
- **Mixer Operations**: Control mixer channels, effects, and routing
- **Export Functions**: Export projects to various formats
- **Plugin Search**: Find and recommend VST plugins and instruments

### 🎨 Emotional Design & Animations
Following modern design principles from successful apps like Duolingo and Revolut:

- **Gradient Backgrounds**: Beautiful color transitions and visual depth
- **Smooth Animations**: Messages fade and slide in with easing curves
- **Pulsing Indicators**: Animated typing indicator with synchronized dots
- **Avatar System**: User and AI avatars with distinct styling
- **Responsive Design**: Adapts to window resizing and screen changes

### 🧠 Agentic AI Capabilities
Built following advanced agentic AI principles:

- **Autonomous Decision Making**: AI can analyze situations and take appropriate actions
- **Planning & Persistence**: Breaks down complex tasks into steps and executes them
- **Learning from Context**: Adapts responses based on project state and user patterns
- **Tool Chaining**: Combines multiple tools to accomplish complex workflows
- **Error Recovery**: Handles failures gracefully and suggests alternatives

## Usage

### Activation
- **Keyboard Shortcut**: Press `Ctrl+8` to toggle the AI sidebar
- **Menu Access**: View → AI Assistant
- **First Time**: Set your GPT-5 API key in the settings

### Example Interactions

**Project Analysis**:
```
"Analyze my current project and suggest improvements"
```

**Creative Assistance**:
```
"Generate a drum pattern in the style of trap music, 4 bars, in A minor"
```

**Technical Help**:
```
"The mix sounds muddy, what can I do to clean it up?"
```

**Workflow Automation**:
```
"Export this project as both WAV and MP3 to my Desktop"
```

## Technical Architecture

### Core Components
- **AiSidebar**: Main UI widget with modern design
- **AiMessage**: Individual message components with animations
- **AiToolResult**: Standardized tool execution results
- **AiSidebarController**: Global singleton for project-wide access

### GPT-5 Integration Details
- **Reasoning Context**: Uses `previous_response_id` for maintaining reasoning chains
- **Minimal Effort Mode**: Optimized for fast responses on simple tasks
- **Custom Tools**: Leverages freeform input for flexible tool calling
- **Allowed Tools**: Constrains tool usage for safety and predictability

### Network Architecture
- Qt5 Network for HTTP/HTTPS requests
- JSON-based communication with OpenAI API
- Asynchronous request handling with proper error management
- Secure API key storage in LMMS configuration

## Installation & Build

### Prerequisites
- Qt5 (5.9.0+) with Network component
- C++17 compatible compiler
- CMake 3.13+
- Valid GPT-5 API key from OpenAI

### Build Instructions
The AI sidebar is integrated into the main LMMS build system:

```bash
cd lmms
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### Configuration
1. Launch LMMS
2. Press `Ctrl+8` to open AI sidebar
3. Enter your GPT-5 API key when prompted
4. Start chatting with your AI assistant!

## API Key Setup

### Getting a GPT-5 API Key
1. Visit https://platform.openai.com
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the key (keep it secure!)

### Setting the Key in LMMS
- The sidebar will prompt you on first use
- Keys are stored securely in LMMS configuration
- Can be updated through the sidebar interface

## Advanced Features

### Agentic Workflows
The AI can handle complex multi-step tasks:

```
"I want to create a full song arrangement. Start with a basic chord progression in C major, add a drum pattern, then suggest a melody line"
```

The AI will:
1. Analyze your current project
2. Create a chord progression track
3. Add appropriate drum patterns
4. Generate melodic suggestions
5. Provide mixing recommendations

### Emotional Feedback
The interface provides delightful interactions:
- Messages animate in with smooth transitions
- Typing indicators create anticipation
- Success/error states are clearly communicated
- Avatar expressions change based on context

### Performance Optimization
- Efficient memory management
- Asynchronous processing
- Smart caching of API responses
- Minimal UI thread blocking

## Troubleshooting

### Common Issues

**API Key Problems**:
- Ensure your API key is valid and has GPT-5 access
- Check your OpenAI account billing status
- Verify network connectivity

**UI Issues**:
- Restart LMMS if sidebar doesn't appear
- Check Qt5 Network component installation
- Ensure proper permissions for network access

**Performance Issues**:
- Reduce reasoning effort for faster responses
- Use lower verbosity for shorter answers
- Check available system memory

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export LMMS_AI_DEBUG=1
./lmms
```

## Security Considerations

### API Key Protection
- Keys stored encrypted in local configuration
- Never transmitted in logs or debug output
- Option to use environment variables for deployment

### Network Security
- All API calls use HTTPS encryption
- Request/response validation
- Rate limiting to prevent abuse

### Tool Safety
- Sandboxed tool execution
- Whitelist of allowed operations
- User confirmation for destructive actions

## Future Enhancements

### Planned Features
- **Voice Integration**: Speech-to-text and text-to-speech
- **Visual Analysis**: AI analysis of waveforms and spectrograms
- **Collaborative Features**: Share AI conversations and suggestions
- **Custom Tool Extensions**: User-defined tools and workflows
- **Learning Preferences**: AI adapts to your production style

### Community Integration
- Plugin marketplace recommendations
- Style analysis and suggestions
- Collaborative project features
- Educational content and tutorials

## Contributing

### Development Setup
1. Fork the LMMS repository
2. Create a feature branch
3. Implement your changes
4. Add comprehensive tests
5. Submit a pull request

### Code Style
- Follow existing LMMS C++ conventions
- Use Qt5 best practices
- Include proper documentation
- Maintain backward compatibility

### Testing
Run the test suite:
```bash
cd build
make test
```

For AI sidebar specific tests:
```bash
./test_ai_sidebar
```

## Credits

### Design Inspiration
- **Duolingo**: Emotional design and character animations
- **Revolut**: Premium visual language and smooth interactions  
- **Phantom**: Approachable crypto UX and playful animations

### Technology Stack
- **GPT-5**: Advanced reasoning and tool calling capabilities
- **Qt5**: Cross-platform UI framework with modern components
- **C++17**: High-performance native implementation
- **CMake**: Reliable build system integration

### Agentic AI Principles
Implementation follows best practices from leading AI research:
- Autonomous decision making
- Tool usage optimization
- Context-aware interactions
- Error handling and recovery

## License

This feature is part of LMMS and released under the same GPL license. See the main LMMS LICENSE file for complete terms.

## Support

### Getting Help
- **Documentation**: This README and inline help
- **Community**: LMMS Discord server and forums
- **Issues**: GitHub issue tracker for bug reports
- **API Questions**: OpenAI documentation and support

### Feedback
We'd love to hear about your experience with the AI assistant:
- Feature requests
- Bug reports  
- Usage examples
- Performance feedback

---

*The future of music production is here. Let AI amplify your creativity!* 🎵✨