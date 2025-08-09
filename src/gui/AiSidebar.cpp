#include "AiSidebar.h"
#include "MainWindow.h"
#include "Song.h"
#include "Engine.h"
#include "Mixer.h"
#include "Track.h"
#include "InstrumentTrack.h"
#include "MidiClip.h"
#include "SampleTrack.h"
#include "SampleClip.h"
#include "Effect.h"
#include "Note.h"
#include "PatternClip.h"
#include "AutomationClip.h"
#include "AudioEngine.h"
#include "ConfigManager.h"
#include "embed.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QScrollArea>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QPropertyAnimation>
#include <QGraphicsOpacityEffect>
#include <QGraphicsDropShadowEffect>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QTimer>
#include <QEasingCurve>
#include <QPainter>
#include <QStyleOption>
#include <QFileInfo>
#include <QDir>
#include <QScrollBar>
#include <QUuid>

namespace lmms::gui
{

// AiMessage Implementation
AiMessage::AiMessage(const QString& content, Role role, QWidget* parent)
    : QWidget(parent)
    , m_content(content)
    , m_role(role)
{
    setupUI();
    
    // Set up opacity effect for smooth animation
    m_opacityEffect = new QGraphicsOpacityEffect(this);
    setGraphicsEffect(m_opacityEffect);
    m_opacityEffect->setOpacity(1.0); // Start visible
    
    // Ensure proper sizing
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::MinimumExpanding);
    setVisible(true);
}

void AiMessage::setupUI()
{
    auto* layout = new QHBoxLayout(this);
    layout->setContentsMargins(12, 8, 12, 8);
    layout->setSpacing(12);
    
    // Avatar (minimal, subtle accent)
    auto* avatarContainer = new QWidget(this);
    avatarContainer->setFixedSize(28, 28);
    avatarContainer->setStyleSheet(
        m_role == User ?
        "background: rgba(124, 58, 237, 0.15); "
        "border: 1px solid rgba(124, 58, 237, 0.35); "
        "border-radius: 14px;" :
        "background: rgba(240, 147, 251, 0.12); "
        "border: 1px solid rgba(240, 147, 251, 0.32); "
        "border-radius: 14px;"
    );
    
    auto* avatarLabel = new QLabel(m_role == User ? "U" : "AI", avatarContainer);
    avatarLabel->setAlignment(Qt::AlignCenter);
    avatarLabel->setStyleSheet("color: rgba(255,255,255,0.9); font-weight: 600; font-size: 11px;");
    avatarLabel->setGeometry(0, 0, 28, 28);
    
    // Message bubble (modern, minimal surface)
    auto* messageWidget = new QWidget(this);
    messageWidget->setStyleSheet(
        m_role == User ?
        "background: rgba(18, 20, 23, 0.9); "
        "border: 1px solid rgba(124, 58, 237, 0.25); "
        "border-radius: 10px; "
        "padding: 8px;" :
        "background: rgba(12, 14, 18, 0.9); "
        "border: 1px solid rgba(255, 255, 255, 0.06); "
        "border-radius: 10px; "
        "padding: 8px;"
    );

    // Removed shadow effect to prevent QPainter conflicts with opacity effect
    
    auto* messageLabel = new QLabel(m_content, messageWidget);
    messageLabel->setWordWrap(true);
    messageLabel->setStyleSheet("color: rgba(255,255,255,0.92); font-size: 13px; padding: 6px;");
    messageLabel->setTextFormat(Qt::RichText);
    messageLabel->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::MinimumExpanding);
    messageLabel->setMinimumHeight(20);
    
    auto* msgLayout = new QVBoxLayout(messageWidget);
    msgLayout->addWidget(messageLabel);
    msgLayout->setContentsMargins(8, 8, 8, 8);
    
    // Ensure message widget has proper sizing
    messageWidget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::MinimumExpanding);
    messageWidget->setMinimumHeight(40);
    
    if (m_role == User) {
        layout->addStretch();
        layout->addWidget(messageWidget, 0);
        layout->addWidget(avatarContainer);
    } else {
        layout->addWidget(avatarContainer);
        layout->addWidget(messageWidget, 1);
        layout->addStretch();
    }
}

void AiMessage::animateIn()
{
    // Ensure message is visible immediately, then animate
    m_opacityEffect->setOpacity(1.0);
    setVisible(true);
    
    // Simple fade animation
    auto* animation = new QPropertyAnimation(m_opacityEffect, "opacity", this);
    animation->setDuration(300);
    animation->setStartValue(0.8);
    animation->setEndValue(1.0);
    animation->setEasingCurve(QEasingCurve::OutQuad);
    animation->start(QAbstractAnimation::DeleteWhenStopped);
}

// AiSidebar Implementation
AiSidebar::AiSidebar(QWidget* parent)
    : QWidget(parent)
    , m_networkManager(std::make_unique<QNetworkAccessManager>(this))
    , m_currentReply(nullptr)
    , m_isProcessing(false)
{
    setupUI();
    setupAnimations();
    
    // Initialize AI Agent for intelligent orchestration
    m_aiAgent = std::make_unique<AiAgent>(this, this);
    
    // Connect AiAgent signals
    connect(m_aiAgent.get(), &AiAgent::toolSequenceReady, 
            this, [this](const QJsonArray& sequence) {
                addMessage(QString("Executing %1 tool sequence steps").arg(sequence.size()), AiMessage::System);
            });
    
    connect(m_aiAgent.get(), &AiAgent::executionCompleted,
            this, [this](bool success, const QString& summary) {
                addMessage(summary, success ? AiMessage::System : AiMessage::System);
                if (success) {
                    addMessage("Complex music generation completed successfully!", AiMessage::Assistant);
                }
                m_isProcessing = false;
                hideTypingIndicator();
            });
    
    connect(m_aiAgent.get(), &AiAgent::errorRecoveryNeeded,
            this, [this](const QString& error, const QJsonArray& suggestions) {
                addMessage(QString("Error: %1. Recovery suggestions available.").arg(error), AiMessage::System);
            });
    
    connect(m_networkManager.get(), &QNetworkAccessManager::finished,
            this, &AiSidebar::onNetworkReply);
    
    // Load API key from config / env / .envs
    QVariant apiKeyVariant = ConfigManager::inst()->value("ai", "gpt5_api_key");
    if (apiKeyVariant.isValid()) {
        m_apiKey = apiKeyVariant.toString();
    }
    if (m_apiKey.isEmpty()) {
        const QByteArray envKey = qgetenv("OPENAI_API_KEY");
        if (!envKey.isEmpty()) {
            m_apiKey = QString::fromUtf8(envKey);
        } else {
            const QStringList candidates = {
                QDir::current().filePath(".envs"),
                QDir::current().filePath("../.envs"),
                QDir::current().filePath("../../.envs")
            };
            for (const QString& path : candidates) {
                QFile f(path);
                if (f.exists() && f.open(QIODevice::ReadOnly | QIODevice::Text)) {
                    QTextStream in(&f);
                    while (!in.atEnd()) {
                        const QString line = in.readLine();
                        if (line.trimmed().startsWith("OPENAI_API_KEY=")) {
                            const auto parts = line.split('=');
                            if (parts.size() >= 2) {
                                m_apiKey = parts.mid(1).join("=");
                                m_apiKey = m_apiKey.trimmed();
                            }
                            break;
                        }
                    }
                    f.close();
                    if (!m_apiKey.isEmpty()) break;
                }
            }
        }
    }
}

AiSidebar::~AiSidebar()
{
    if (m_currentReply) {
        m_currentReply->abort();
        m_currentReply->deleteLater();
    }
}

void AiSidebar::setupUI()
{
    setFixedWidth(380);
    setStyleSheet(
        "QWidget { "
        "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 #0a0c10, stop:1 #0e1116); "
        "border-left: 1px solid rgba(255,255,255,0.06); "
        "}"
    );
    
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setSpacing(0);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    
    // Header with animated gradient
    auto* header = new QWidget(this);
    header->setFixedHeight(52);
    header->setStyleSheet(
        "background: rgba(0,0,0,0.15); "
        "border-bottom: 1px solid rgba(255, 255, 255, 0.06);"
    );
    
    auto* headerLayout = new QHBoxLayout(header);
    auto* titleLabel = new QLabel("AI", header);
    titleLabel->setStyleSheet(
        "color: rgba(255,255,255,0.92); "
        "font-size: 15px; "
        "font-weight: 600; "
    );
    
    auto* statusLabel = new QLabel("GPT‑5", header);
    statusLabel->setStyleSheet(
        "color: rgba(20, 184, 166, 0.95); "
        "font-size: 11px; "
        "background: rgba(20,184,166,0.12); "
        "padding: 3px 8px; "
        "border: 1px solid rgba(20,184,166,0.28); "
        "border-radius: 9px;"
    );
    
    headerLayout->addWidget(titleLabel);
    headerLayout->addStretch();
    headerLayout->addWidget(statusLabel);
    
    // Messages area with custom scrollbar
    m_scrollArea = new QScrollArea(this);
    m_scrollArea->setWidgetResizable(true);
    m_scrollArea->setStyleSheet(
        "QScrollArea { "
        "background: transparent; "
        "border: none; "
        "}"
        "QScrollBar:vertical { "
        "background: transparent; "
        "width: 6px; "
        "margin: 4px 2px 4px 2px;"
        "}"
        "QScrollBar::handle:vertical { "
        "background: rgba(255,255,255,0.14); "
        "border-radius: 3px; "
        "min-height: 24px; "
        "}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
    );
    
    m_messagesContainer = new QWidget();
    m_messagesLayout = new QVBoxLayout(m_messagesContainer);
    m_messagesLayout->setSpacing(12);
    m_messagesLayout->setContentsMargins(12, 12, 12, 12);
    m_messagesLayout->addStretch();
    
    m_scrollArea->setWidget(m_messagesContainer);
    
    // Typing indicator with pulsing animation
    m_typingIndicator = new QWidget(this);
    m_typingIndicator->setFixedHeight(36);
    m_typingIndicator->setVisible(false);
    m_typingIndicator->setStyleSheet(
        "background: rgba(255, 255, 255, 0.04); "
        "border: 1px solid rgba(255, 255, 255, 0.06); "
        "border-radius: 18px; "
        "margin: 0 12px;"
    );
    
    auto* typingLayout = new QHBoxLayout(m_typingIndicator);
    for (int i = 0; i < 3; ++i) {
        auto* dot = new QLabel("•", m_typingIndicator);
        dot->setStyleSheet("color: rgba(255,255,255,0.5); font-size: 18px;");
        typingLayout->addWidget(dot);
    }
    
    // Input area with modern design
    auto* inputContainer = new QWidget(this);
    inputContainer->setFixedHeight(72);
    inputContainer->setStyleSheet(
        "background: rgba(0, 0, 0, 0.18); "
        "border-top: 1px solid rgba(255, 255, 255, 0.06);"
    );
    
    auto* inputLayout = new QHBoxLayout(inputContainer);
    inputLayout->setContentsMargins(12, 12, 12, 12);
    inputLayout->setSpacing(12);
    
    m_inputField = new QLineEdit(inputContainer);
    m_inputField->setPlaceholderText("Ask or instruct…");
    m_inputField->setStyleSheet(
        "QLineEdit { "
        "background: rgba(255, 255, 255, 0.06); "
        "border: 1px solid rgba(255, 255, 255, 0.12); "
        "border-radius: 16px; "
        "padding: 10px 14px; "
        "color: rgba(255,255,255,0.92); "
        "font-size: 13px; "
        "}"
        "QLineEdit:focus { "
        "border: 1px solid rgba(124, 58, 237, 0.6); "
        "background: rgba(255, 255, 255, 0.10); "
        "}"
    );
    
    m_sendButton = new QPushButton("Send", inputContainer);
    m_sendButton->setFixedSize(76, 40);
    m_sendButton->setStyleSheet(
        "QPushButton { "
        "background: rgba(124, 58, 237, 0.18); "
        "border: 1px solid rgba(124, 58, 237, 0.4); "
        "border-radius: 12px; "
        "color: rgba(255,255,255,0.95); "
        "font-weight: 600; "
        "font-size: 13px; "
        "}"
        "QPushButton:hover { "
        "background: rgba(124, 58, 237, 0.26); "
        "}"
        "QPushButton:pressed { "
        "background: rgba(124, 58, 237, 0.35); "
        "}"
    );
    
    inputLayout->addWidget(m_inputField);
    inputLayout->addWidget(m_sendButton);
    
    // Assemble main layout
    mainLayout->addWidget(header);
    mainLayout->addWidget(m_scrollArea, 1);
    mainLayout->addWidget(m_typingIndicator);
    mainLayout->addWidget(inputContainer);
    
    // Connect signals
    connect(m_sendButton, &QPushButton::clicked, this, &AiSidebar::onSendMessage);
    connect(m_inputField, &QLineEdit::returnPressed, this, &AiSidebar::onSendMessage);
    
    // Add welcome message for testing
    QTimer::singleShot(500, [this]() {
        addMessage("🎵 AI Agent Ready! Try: 'Create a Fred again style house beat'", AiMessage::System);
    });
}

void AiSidebar::setupAnimations()
{
    // Slide animation for sidebar visibility
    m_slideAnimation = new QPropertyAnimation(this, "pos", this);
    m_slideAnimation->setDuration(300);
    m_slideAnimation->setEasingCurve(QEasingCurve::OutCubic);
    
    // Fade animation for messages
    m_fadeAnimation = new QPropertyAnimation(this, "windowOpacity", this);
    m_fadeAnimation->setDuration(200);
    m_fadeAnimation->setEasingCurve(QEasingCurve::InOutQuad);
}

void AiSidebar::toggleVisibility()
{
    if (isVisible()) {
        m_slideAnimation->setStartValue(pos());
        m_slideAnimation->setEndValue(QPoint(parentWidget()->width(), pos().y()));
        connect(m_slideAnimation, &QPropertyAnimation::finished, this, &QWidget::hide);
        m_slideAnimation->start();
    } else {
        show();
        m_slideAnimation->setStartValue(QPoint(parentWidget()->width(), pos().y()));
        m_slideAnimation->setEndValue(QPoint(parentWidget()->width() - width(), pos().y()));
        m_slideAnimation->start();
    }
    
    emit visibilityChanged(isVisible());
}

void AiSidebar::setApiKey(const QString& key)
{
    m_apiKey = key;
    ConfigManager::inst()->setValue("ai", "gpt5_api_key", key);
}

void AiSidebar::sendMessage(const QString& message)
{
    sendToGPT5(message);
}

void AiSidebar::onSendMessage()
{
    QString message = m_inputField->text().trimmed();
    if (message.isEmpty() || m_isProcessing) {
        qDebug() << "Message empty or already processing";
        return;
    }
    
    qDebug() << "Sending message:" << message;
    
    m_inputField->clear();
    addMessage(message, AiMessage::User);
    
    m_isProcessing = true;
    showTypingIndicator();
    
    // Add a small delay to ensure UI updates
    QTimer::singleShot(100, [this, message]() {
        sendToGPT5(message);
    });
}

void AiSidebar::sendToGPT5(const QString& message)
{
    if (m_apiKey.isEmpty()) {
        addMessage("⚠️ No GPT-5 API key found. Set OPENAI_API_KEY in environment or .envs file.", AiMessage::System);
        addMessage("For testing: You can still use local AI agent features!", AiMessage::Assistant);
        hideTypingIndicator();
        m_isProcessing = false;
        return;
    }
    
    // Use AI Agent for intelligent processing first
    if (!message.isEmpty()) {
        // Check if this is a complex beatmaking/music creation request
        QString lowerMsg = message.toLower();
        bool isComplexMusicRequest = (
            lowerMsg.contains("make") || lowerMsg.contains("create") || lowerMsg.contains("build")
        ) && (
            lowerMsg.contains("beat") || lowerMsg.contains("track") || lowerMsg.contains("song") ||
            lowerMsg.contains("house") || lowerMsg.contains("fred again") || lowerMsg.contains("garage") ||
            lowerMsg.contains("drum") || lowerMsg.contains("bass") || lowerMsg.contains("pattern")
        );
        
        if (isComplexMusicRequest && m_aiAgent) {
            try {
                // Use AiAgent for intelligent orchestration
                addMessage("🤖 Processing with AI Agent: " + message.left(50) + "...", AiMessage::System);
                m_aiAgent->processUserIntent(message);
                return; // Agent will handle the rest
            } catch (const std::exception& e) {
                addMessage(QString("AI Agent Error: %1").arg(e.what()), AiMessage::System);
                addMessage("Falling back to direct GPT-5 processing...", AiMessage::System);
                // Continue to GPT-5 processing below
            }
        }
    }
    
    // Build conversation for GPT-5 fallback
    if (!message.isEmpty()) {
        QJsonObject userMessage;
        userMessage["role"] = "user";
        userMessage["content"] = message;
        m_conversationHistory.append(userMessage);
    }
    
    // Prepare GPT-5 request with new parameters
    QJsonObject requestBody;
    // Enforce GPT-5 exclusively per project policy
    requestBody["model"] = QStringLiteral("gpt-5");
    // Build a per-request input with a routing system message so broad NL queries map to tools
    QJsonArray requestInput;
    {
        QString toolGuide =
            "You are the LMMS AI agent. Interpret natural language into concrete, multi-step DAW actions. "
            "Plan briefly, then call tools to modify the project. If the user asks broadly (e.g., 'make a house track like X'), "
            "break it down (tempo, tracks, clips, notes, effects, arrangement) and chain tool calls until done. "
            "Available tools: read_project, modify_track, add_instrument, set_tempo, create_track, create_midi_clip, write_notes, add_sample_clip, add_effect, move_clip, analyze_audio, mixer_control, export_project, search_plugin, generate_pattern. "
            "Prefer minimal reasoning; only ask for clarification when truly ambiguous. Output tool calls as needed until the goal is satisfied.";
        QJsonObject sysMsg; sysMsg["role"] = "system"; sysMsg["content"] = toolGuide;
        requestInput.append(sysMsg);
        if (m_gpt5Settings.usePreambles) {
            QJsonObject sysPreamble; sysPreamble["role"] = "system";
            sysPreamble["content"] = "Before any tool call, briefly state what you will do and why.";
            requestInput.append(sysPreamble);
        }
    }
    for (const auto& v : m_conversationHistory) { requestInput.append(v); }
    requestBody["input"] = requestInput;
    
    // Add reasoning settings
    QJsonObject reasoning;
    reasoning["effort"] = m_gpt5Settings.reasoningEffort;
    requestBody["reasoning"] = reasoning;
    
    // Add text settings
    QJsonObject textSettings;
    textSettings["verbosity"] = m_gpt5Settings.verbosity;
    requestBody["text"] = textSettings;
    
    // Add previous response ID for reasoning context
    if (!m_previousResponseId.isEmpty()) {
        requestBody["previous_response_id"] = m_previousResponseId;
    }
    
    // Add tool definitions
    requestBody["tools"] = getToolDefinitions();
    
    // Tool choice with allowed tools
    QJsonObject toolChoice;
    toolChoice["type"] = "allowed_tools";
    toolChoice["mode"] = "auto";
    toolChoice["tools"] = m_gpt5Settings.allowedTools.isEmpty() ? 
                          getToolDefinitions() : m_gpt5Settings.allowedTools;
    requestBody["tool_choice"] = toolChoice;
    
    // Add preamble instruction if enabled
    if (m_gpt5Settings.usePreambles) {
        QJsonObject systemMessage;
        systemMessage["role"] = "system";
        systemMessage["content"] = "Before calling any tool, briefly explain what you're about to do and why.";
        // Ensure preamble appears before most recent message for this turn
        m_conversationHistory.append(systemMessage);
    }
    
    QNetworkRequest request(QUrl("https://api.openai.com/v1/responses"));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setRawHeader("Authorization", QString("Bearer %1").arg(m_apiKey).toUtf8());
    
    QJsonDocument doc(requestBody);
    m_currentReply = m_networkManager->post(request, doc.toJson());
}

void AiSidebar::onNetworkReply()
{
    if (!m_currentReply) return;
    
    QByteArray response = m_currentReply->readAll();
    m_currentReply->deleteLater();
    m_currentReply = nullptr;
    
    QJsonDocument doc = QJsonDocument::fromJson(response);
    QJsonObject responseObj = doc.object();
    
    if (responseObj.contains("error")) {
        QString error = responseObj["error"].toObject()["message"].toString();
        addMessage("Error: " + error, AiMessage::System);
        hideTypingIndicator();
        m_isProcessing = false;
        return;
    }
    
    processGPT5Response(responseObj);
}

void AiSidebar::processGPT5Response(const QJsonObject& response)
{
    // Extract response ID for reasoning context
    if (response.contains("id")) {
        m_previousResponseId = response["id"].toString();
    }
    
    // Process output array
    QJsonArray output = response["output"].toArray();
    
    for (const QJsonValue& item : output) {
        QJsonObject outputItem = item.toObject();
        QString type = outputItem["type"].toString();
        
        if (type == "message") {
            // Extract text content
            QJsonArray content = outputItem["content"].toArray();
            QString messageText;
            
            for (const QJsonValue& contentItem : content) {
                QJsonObject contentObj = contentItem.toObject();
                if (contentObj["type"].toString() == "output_text") {
                    messageText += contentObj["text"].toString();
                }
            }
            
            if (!messageText.isEmpty()) {
                hideTypingIndicator();
                addMessage(messageText, AiMessage::Assistant);
            }
        }
        else if (type == "function_call") {
            // Handle tool call
            executeToolCall(outputItem);
        }
        else if (type == "reasoning") {
            // Optionally show reasoning summary if verbose
            if (m_gpt5Settings.verbosity == "high") {
                QJsonArray summary = outputItem["summary"].toArray();
                for (const QJsonValue& summaryItem : summary) {
                    QJsonObject summaryObj = summaryItem.toObject();
                    if (summaryObj["type"].toString() == "summary_text") {
                        QString reasoningText = summaryObj["text"].toString();
                        addMessage("Thinking: " + reasoningText, AiMessage::System);
                    }
                }
            }
        }
    }
    
    hideTypingIndicator();
    m_isProcessing = false;
}

void AiSidebar::executeToolCall(const QJsonObject& toolCall)
{
    QString toolName = toolCall["name"].toString();
    QJsonObject arguments = QJsonDocument::fromJson(
        toolCall["arguments"].toString().toUtf8()
    ).object();
    
    AiToolResult result;
    result.toolName = toolName;
    result.input = arguments;
    
    // Show tool preamble if available
    if (toolCall.contains("preamble")) {
        addMessage(toolCall["preamble"].toString(), AiMessage::System);
    }
    
    // Execute appropriate tool
    if (toolName == "read_project") {
        result = executeReadProjectTool(arguments);
    }
    else if (toolName == "modify_track") {
        result = executeModifyTrackTool(arguments);
    }
    else if (toolName == "add_instrument") {
        result = executeAddInstrumentTool(arguments);
    }
    else if (toolName == "analyze_audio") {
        result = executeAnalyzeAudioTool(arguments);
    }
    else if (toolName == "generate_pattern") {
        result = executeGeneratePatternTool(arguments);
    }
    else if (toolName == "mixer_control") {
        result = executeMixerControlTool(arguments);
    }
    else if (toolName == "export_project") {
        result = executeExportProjectTool(arguments);
    }
    else if (toolName == "search_plugin") {
        result = executeSearchPluginTool(arguments);
    }
    else if (toolName == "set_tempo") {
        result = executeSetTempoTool(arguments);
    }
    else if (toolName == "create_midi_clip") {
        result = executeCreateMidiClipTool(arguments);
    }
    else if (toolName == "write_notes") {
        result = executeWriteNotesTool(arguments);
    }
    else if (toolName == "add_effect") {
        result = executeAddEffectTool(arguments);
    }
    else if (toolName == "add_sample_clip") {
        result = executeAddSampleClipTool(arguments);
    }
    else if (toolName == "create_track") {
        result = executeCreateTrackTool(arguments);
    }
    else if (toolName == "move_clip") {
        result = executeMoveClipTool(arguments);
    }
    else if (toolName == "create_automation_clip") {
        result = executeCreateAutomationClipTool(arguments);
    }
    else if (toolName == "create_section") {
        result = executeCreateSectionTool(arguments);
    }
    else if (toolName == "duplicate_section") {
        result = executeDuplicateSectionTool(arguments);
    }
    else if (toolName == "mutate_section") {
        result = executeMutateSectionTool(arguments);
    }
    else if (toolName == "sidechain_pump_automation") {
        result = executeSidechainPumpAutomationTool(arguments);
    }
    else if (toolName == "quantize_notes") {
        result = executeQuantizeNotesTool(arguments);
    }
    else if (toolName == "apply_groove") {
        result = executeApplyGrooveTool(arguments);
    }
    else if (toolName == "duplicate_clip") {
        result = executeDuplicateClipTool(arguments);
    }
    
    onToolExecutionComplete(result);
}

void AiSidebar::onToolExecutionComplete(const AiToolResult& result)
{
    // If AiAgent is handling this, notify it
    if (m_aiAgent) {
        m_aiAgent->handleToolResult(result);
        return; // Agent handles the rest
    }
    
    // Original behavior for non-agent tool execution
    QString feedback = QString("Tool '%1' executed: %2")
        .arg(result.toolName)
        .arg(result.success ? "Success" : "Failed");
    
    if (!result.output.isEmpty()) {
        feedback += "\n" + result.output;
    }
    
    addMessage(feedback, AiMessage::System);
    
    // Continue conversation with tool result
    QJsonObject toolResult;
    toolResult["tool_use_id"] = QUuid::createUuid().toString();
    toolResult["content"] = result.output;
    
    // Send tool result back to GPT-5
    if (result.success && m_isProcessing) {
        // Build follow-up request with tool result
        QJsonObject followUp;
        followUp["role"] = "tool";
        followUp["content"] = toolResult;
        m_conversationHistory.append(followUp);
        
        // Continue conversation
        sendToGPT5("");
    }
}

AiToolResult AiSidebar::executeReadProjectTool(const QJsonObject& params)
{
    AiToolResult result;
    result.toolName = "read_project";
    
    try {
        Song* song = Engine::getSong();
        if (!song) {
            result.success = false;
            result.output = "No project is currently open";
            return result;
        }
        
        QJsonObject projectInfo;
        projectInfo["name"] = song->projectFileName();
        projectInfo["tempo"] = song->getTempo();
        projectInfo["time_signature"] = QString("%1/%2")
            .arg(song->getTimeSigModel().getNumerator())
            .arg(song->getTimeSigModel().getDenominator());
        projectInfo["master_volume"] = song->masterVolume();
        projectInfo["master_pitch"] = song->masterPitch();
        
        // Get track information
        QJsonArray tracks;
        for (Track* track : song->tracks()) {
            QJsonObject trackInfo;
            trackInfo["name"] = track->name();
            trackInfo["type"] = static_cast<int>(track->type());
            trackInfo["muted"] = track->isMuted();
            trackInfo["solo"] = track->isSolo();
            tracks.append(trackInfo);
        }
        projectInfo["tracks"] = tracks;
        
        result.success = true;
        result.output = QJsonDocument(projectInfo).toJson(QJsonDocument::Compact);
    }
    catch (const std::exception& e) {
        result.success = false;
        result.output = QString("Error: %1").arg(e.what());
    }
    
    return result;
}

AiToolResult AiSidebar::executeModifyTrackTool(const QJsonObject& params)
{
    AiToolResult result;
    result.toolName = "modify_track";
    
    QString trackName = params["track_name"].toString();
    QString action = params["action"].toString();
    
    Song* song = Engine::getSong();
    if (!song) {
        result.success = false;
        result.output = "No project is currently open";
        return result;
    }
    
    // Find track by name
    Track* targetTrack = nullptr;
    for (Track* track : song->tracks()) {
        if (track->name() == trackName) {
            targetTrack = track;
            break;
        }
    }
    
    if (!targetTrack) {
        result.success = false;
        result.output = QString("Track '%1' not found").arg(trackName);
        return result;
    }
    
    // Execute action
    if (action == "mute") {
        targetTrack->setMuted(true);
        result.success = true;
        result.output = QString("Track '%1' muted").arg(trackName);
    }
    else if (action == "unmute") {
        targetTrack->setMuted(false);
        result.success = true;
        result.output = QString("Track '%1' unmuted").arg(trackName);
    }
    else if (action == "solo") {
        targetTrack->setSolo(true);
        result.success = true;
        result.output = QString("Track '%1' soloed").arg(trackName);
    }
    else if (action == "rename") {
        QString newName = params["new_name"].toString();
        targetTrack->setName(newName);
        result.success = true;
        result.output = QString("Track renamed to '%1'").arg(newName);
    }
    else {
        result.success = false;
        result.output = QString("Unknown action: %1").arg(action);
    }
    
    return result;
}

AiToolResult AiSidebar::executeAddInstrumentTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "add_instrument";
    const QString instrumentName = params.value("instrument").toString();
    const QString trackName = params.value("track_name").toString("New Instrument");

    Song* song = Engine::getSong();
    if (!song) { result.success = false; result.output = "No project is currently open"; return result; }

    // Reuse or create
    InstrumentTrack* it = nullptr;
    for (Track* t : song->tracks()) { if (t->name() == trackName) { it = dynamic_cast<InstrumentTrack*>(t); break; } }
    if (!it) {
        it = dynamic_cast<InstrumentTrack*>(Track::create(Track::Type::Instrument, song));
        if (!it) { result.success = false; result.output = "Failed to create instrument track"; return result; }
        it->setName(trackName);
    }
    if (!instrumentName.isEmpty()) {
        Instrument* inst = it->loadInstrument(instrumentName);
        if (!inst) { result.success = false; result.output = QString("Failed to load instrument '%1'").arg(instrumentName); return result; }
    }
    result.success = true;
    result.output = instrumentName.isEmpty() ? QString("Created instrument track '%1'").arg(trackName)
                                             : QString("Instrument '%1' loaded on '%2'").arg(instrumentName, trackName);
    return result;
}

AiToolResult AiSidebar::executeAnalyzeAudioTool(const QJsonObject& params)
{
    AiToolResult result;
    result.toolName = "analyze_audio";
    
    // Perform audio analysis
    AudioEngine* audioEngine = Engine::audioEngine();
    if (!audioEngine) {
        result.success = false;
        result.output = "Audio engine not available";
        return result;
    }
    
    QJsonObject analysis;
    analysis["sample_rate"] = static_cast<int>(audioEngine->outputSampleRate());
    analysis["buffer_size"] = static_cast<int>(audioEngine->framesPerPeriod());
    analysis["cpu_load"] = audioEngine->cpuLoad();
    
    result.success = true;
    result.output = QJsonDocument(analysis).toJson(QJsonDocument::Compact);
    
    return result;
}

AiToolResult AiSidebar::executeGeneratePatternTool(const QJsonObject& params)
{
    AiToolResult result;
    result.toolName = "generate_pattern";
    
    QString style = params["style"].toString();
    int bars = params["bars"].toInt(4);
    QString scale = params["scale"].toString("C major");
    
    // Pattern generation logic would go here
    // This is a placeholder implementation
    result.success = true;
    result.output = QString("Generated %1 bars of %2 pattern in %3")
        .arg(bars).arg(style).arg(scale);
    
    return result;
}

AiToolResult AiSidebar::executeMixerControlTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "mixer_control";
    const QString trackName = params.value("track_name").toString();
    const QString parameter = params.value("parameter").toString();
    const double value = params.value("value").toDouble();

    Song* song = Engine::getSong(); if (!song) { result.success = false; result.output = "No project"; return result; }
    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    if (!targetTrack) { result.success = false; result.output = "Track not found"; return result; }

    if (parameter == "mute") { targetTrack->setMuted(value > 0.5); result.success = true; result.output = QString("%1 %2").arg(trackName, value > 0.5 ? "muted" : "unmuted"); return result; }
    if (parameter == "solo") { targetTrack->setSolo(value > 0.5); result.success = true; result.output = QString("%1 %2").arg(trackName, value > 0.5 ? "soloed" : "unsoloed"); return result; }
    if (auto* it = dynamic_cast<InstrumentTrack*>(targetTrack)) {
        if (parameter == "volume") { it->volumeModel()->setValue(static_cast<float>(value)); result.success = true; result.output = QString("%1 volume %2").arg(trackName).arg(value); return result; }
        if (parameter == "pan" || parameter == "panning") { it->panningModel()->setValue(static_cast<float>(value)); result.success = true; result.output = QString("%1 pan %2").arg(trackName).arg(value); return result; }
    }
    result.success = false; result.output = "Unsupported parameter or track type"; return result;
}

AiToolResult AiSidebar::executeExportProjectTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "export_project";
    const QString format = params.value("format").toString("wav");
    const QString path = params.value("path").toString();
    if (path.isEmpty()) { result.success = false; result.output = "Missing path"; return result; }
    Song* song = Engine::getSong(); if (!song) { result.success = false; result.output = "No project"; return result; }
    if (format.toLower() == "midi") { song->exportProjectMidi(path); result.success = true; result.output = QString("MIDI exported to %1").arg(path); return result; }
    result.success = false; result.output = "Audio export via tool not yet implemented (use UI)"; return result;
}

AiToolResult AiSidebar::executeSearchPluginTool(const QJsonObject& params)
{
    AiToolResult result;
    result.toolName = "search_plugin";
    
    QString query = params["query"].toString();
    
    // Plugin search logic would go here
    QJsonArray results;
    // Placeholder results
    QJsonObject plugin1;
    plugin1["name"] = "TripleOscillator";
    plugin1["type"] = "Instrument";
    results.append(plugin1);
    
    result.success = true;
    result.output = QJsonDocument(results).toJson(QJsonDocument::Compact);
    
    return result;
}

void AiSidebar::addMessage(const QString& content, AiMessage::Role role)
{
    if (content.isEmpty()) {
        qDebug() << "Warning: Attempted to add empty message";
        return;
    }
    
    auto* message = new AiMessage(content, role, m_messagesContainer);
    
    // Insert before the stretch item (which should be the last item)
    int insertIndex = qMax(0, m_messagesLayout->count() - 1);
    m_messagesLayout->insertWidget(insertIndex, message);
    
    // Ensure message is visible
    message->show();
    message->animateIn();
    
    // Update container and scroll
    m_messagesContainer->updateGeometry();
    
    // Auto-scroll to bottom with delay to ensure layout is updated
    QTimer::singleShot(150, [this]() {
        if (m_scrollArea && m_scrollArea->verticalScrollBar()) {
            m_scrollArea->verticalScrollBar()->setValue(
                m_scrollArea->verticalScrollBar()->maximum()
            );
        }
    });
    
    qDebug() << "Added message:" << content.left(50) << "Role:" << (role == AiMessage::User ? "User" : (role == AiMessage::Assistant ? "Assistant" : "System"));
}

void AiSidebar::showTypingIndicator()
{
    m_typingIndicator->setVisible(true);
    
    // Animate typing dots
    QTimer* timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, &AiSidebar::onTypingAnimation);
    timer->start(500);
}

void AiSidebar::hideTypingIndicator()
{
    m_typingIndicator->setVisible(false);
}

void AiSidebar::onTypingAnimation()
{
    // Subtle opacity pulse for typing dots
    static int currentDot = 0;
    QLayout* layout = m_typingIndicator->layout();
    
    for (int i = 0; i < layout->count(); ++i) {
        QLabel* dot = qobject_cast<QLabel*>(layout->itemAt(i)->widget());
        if (dot) {
            dot->setStyleSheet(
                i == currentDot ?
                "color: rgba(255,255,255,0.75); font-size: 18px;" :
                "color: rgba(255,255,255,0.45); font-size: 18px;"
            );
        }
    }
    
    currentDot = (currentDot + 1) % 3;
}

QJsonArray AiSidebar::getToolDefinitions() const
{
    QJsonArray tools;
    
    // Read Project Tool
    QJsonObject readProject;
    readProject["type"] = "custom";
    readProject["name"] = "read_project";
    readProject["description"] = "Read current LMMS project information including tracks, tempo, and settings";
    tools.append(readProject);
    
    // Modify Track Tool
    QJsonObject modifyTrack;
    modifyTrack["type"] = "custom";
    modifyTrack["name"] = "modify_track";
    modifyTrack["description"] = "Modify track properties like mute, solo, volume, or rename";
    tools.append(modifyTrack);
    
    // Add Instrument Tool
    QJsonObject addInstrument;
    addInstrument["type"] = "custom";
    addInstrument["name"] = "add_instrument";
    addInstrument["description"] = "Add a new instrument track with specified plugin";
    tools.append(addInstrument);
    
    // Analyze Audio Tool
    QJsonObject analyzeAudio;
    analyzeAudio["type"] = "custom";
    analyzeAudio["name"] = "analyze_audio";
    analyzeAudio["description"] = "Analyze audio properties like frequency spectrum, BPM, or key";
    tools.append(analyzeAudio);
    
    // Generate Pattern Tool
    QJsonObject generatePattern;
    generatePattern["type"] = "custom";
    generatePattern["name"] = "generate_pattern";
    generatePattern["description"] = "Generate musical patterns based on style and parameters";
    tools.append(generatePattern);
    
    // Mixer Control Tool
    QJsonObject mixerControl;
    mixerControl["type"] = "custom";
    mixerControl["name"] = "mixer_control";
    mixerControl["description"] = "Control mixer channels, effects, and routing";
    tools.append(mixerControl);
    
    // Export Project Tool
    QJsonObject exportProject;
    exportProject["type"] = "custom";
    exportProject["name"] = "export_project";
    exportProject["description"] = "Export project to various audio formats";
    tools.append(exportProject);
    
    // Search Plugin Tool
    QJsonObject searchPlugin;
    searchPlugin["type"] = "custom";
    searchPlugin["name"] = "search_plugin";
    searchPlugin["description"] = "Search for VST plugins, instruments, or effects";
    tools.append(searchPlugin);

    // Set Tempo Tool
    QJsonObject setTempo;
    setTempo["type"] = "custom";
    setTempo["name"] = "set_tempo";
    setTempo["description"] = "Set project tempo in BPM";
    tools.append(setTempo);

    // Create MIDI Clip Tool
    QJsonObject createMidiClip;
    createMidiClip["type"] = "custom";
    createMidiClip["name"] = "create_midi_clip";
    createMidiClip["description"] = "Create a MIDI clip on an instrument track at a position and length";
    tools.append(createMidiClip);

    // Write Notes Tool
    QJsonObject writeNotes;
    writeNotes["type"] = "custom";
    writeNotes["name"] = "write_notes";
    writeNotes["description"] = "Write MIDI notes into a clip with positions, lengths, and velocities";
    tools.append(writeNotes);

    // Add Effect Tool
    QJsonObject addEffect;
    addEffect["type"] = "custom";
    addEffect["name"] = "add_effect";
    addEffect["description"] = "Insert an effect plugin on a track's effect chain";
    tools.append(addEffect);

    // Add Sample Clip Tool
    QJsonObject addSampleClip;
    addSampleClip["type"] = "custom";
    addSampleClip["name"] = "add_sample_clip";
    addSampleClip["description"] = "Create a sample clip on a sample track and load audio from file";
    tools.append(addSampleClip);

    // Create Track Tool
    QJsonObject createTrack;
    createTrack["type"] = "custom";
    createTrack["name"] = "create_track";
    createTrack["description"] = "Create a new track (instrument or sample) with a name and optional instrument";
    tools.append(createTrack);

    // Move Clip Tool
    QJsonObject moveClip;
    moveClip["type"] = "custom";
    moveClip["name"] = "move_clip";
    moveClip["description"] = "Move an existing clip to a new start position";
    tools.append(moveClip);

    // Create Automation Clip Tool
    QJsonObject createAuto;
    createAuto["type"] = "custom";
    createAuto["name"] = "create_automation_clip";
    createAuto["description"] = "Create an automation clip on the automation track";
    tools.append(createAuto);

    // Arrangement: Create Section
    QJsonObject createSection;
    createSection["type"] = "custom";
    createSection["name"] = "create_section";
    createSection["description"] = "Create a named section with start and length in ticks";
    tools.append(createSection);

    // Arrangement: Duplicate Section
    QJsonObject duplicateSection;
    duplicateSection["type"] = "custom";
    duplicateSection["name"] = "duplicate_section";
    duplicateSection["description"] = "Duplicate a named section N times sequentially";
    tools.append(duplicateSection);

    // Arrangement: Mutate Section (simple transformations)
    QJsonObject mutateSection;
    mutateSection["type"] = "custom";
    mutateSection["name"] = "mutate_section";
    mutateSection["description"] = "Apply simple mutations to a section (transpose, humanize, thin)";
    tools.append(mutateSection);

    // Automation: Sidechain Pump (parameterized)
    QJsonObject sidechainPump;
    sidechainPump["type"] = "custom";
    sidechainPump["name"] = "sidechain_pump_automation";
    sidechainPump["description"] = "Create an automation curve to duck volume rhythmically (pump)";
    tools.append(sidechainPump);

    // Quantize Notes Tool
    QJsonObject quantizeNotes;
    quantizeNotes["type"] = "custom";
    quantizeNotes["name"] = "quantize_notes";
    quantizeNotes["description"] = "Quantize MIDI notes in a clip to a grid (e.g., 1/16)";
    tools.append(quantizeNotes);

    // Apply Groove Tool
    QJsonObject applyGroove;
    applyGroove["type"] = "custom";
    applyGroove["name"] = "apply_groove";
    applyGroove["description"] = "Apply swing/groove to selected notes (timing offsets)";
    tools.append(applyGroove);

    // Duplicate Clip Tool
    QJsonObject duplicateClip;
    duplicateClip["type"] = "custom";
    duplicateClip["name"] = "duplicate_clip";
    duplicateClip["description"] = "Duplicate a clip N times sequentially in the arrangement";
    tools.append(duplicateClip);
    
    return tools;
}

// --- Concrete tool implementations ---

AiToolResult AiSidebar::executeSetTempoTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "set_tempo"; result.success = false;
    const QJsonValue bpmVal = params.value("bpm");
    if (!bpmVal.isDouble()) { result.output = "Invalid bpm"; return result; }
    const double bpm = bpmVal.toDouble();
    if (bpm <= 0) { result.output = "Invalid bpm"; return result; }
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    song->tempoModel().setValue(static_cast<int>(bpm));
    result.success = true; result.output = QString("Tempo set to %1 BPM").arg(bpm);
    return result;
}

AiToolResult AiSidebar::executeCreateMidiClipTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "create_midi_clip"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int startTicks = params.value("start_ticks").toInt(0);
    const int lengthTicks = params.value("length_ticks").toInt(TimePos::ticksPerBar());

    // Debug: List all available tracks
    qDebug() << "CREATE_MIDI_CLIP: Looking for track:" << trackName;
    qDebug() << "Available tracks:";
    for (Track* t : song->tracks()) { 
        qDebug() << "  - Track name:" << t->name() << "Type:" << (int)t->type();
    }
    
    Track* targetTrack = nullptr;
    for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    if (!targetTrack) { 
        result.output = QString("Track '%1' not found. Available tracks: %2")
                       .arg(trackName)
                       .arg([&]() {
                           QStringList trackNames;
                           for (Track* t : song->tracks()) trackNames << t->name();
                           return trackNames.join(", ");
                       }());
        return result; 
    }

    auto* it = dynamic_cast<InstrumentTrack*>(targetTrack);
    if (!it) { result.output = "Target track is not an instrument track"; return result; }
    MidiClip* clip = dynamic_cast<MidiClip*>(it->createClip(TimePos(startTicks)));
    if (!clip) { result.output = "Failed to create MIDI clip"; return result; }
    clip->changeLength(TimePos(lengthTicks));
    result.success = true; result.output = QString("MIDI clip created at %1 len %2").arg(startTicks).arg(lengthTicks);
    return result;
}

AiToolResult AiSidebar::executeWriteNotesTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "write_notes"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int clipIndex = params.value("clip_index").toInt(0);
    const QJsonArray notes = params.value("notes").toArray();

    Track* targetTrack = nullptr;
    for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    auto* it = dynamic_cast<InstrumentTrack*>(targetTrack);
    if (!it) { result.output = "Instrument track not found"; return result; }

    auto& clips = it->getClips();
    if (clipIndex < 0 || static_cast<size_t>(clipIndex) >= clips.size()) { result.output = "Clip index out of range"; return result; }
    auto* midiClip = dynamic_cast<MidiClip*>(clips[clipIndex]);
    if (!midiClip) { result.output = "Target clip is not MIDI"; return result; }

    for (const auto& n : notes) {
        QJsonObject no = n.toObject();
        int start = no.value("start_ticks").toInt();
        int len = no.value("length_ticks").toInt(TimePos::ticksPerBar() / 4);
        int key = no.value("key").toInt(lmms::DefaultKey);
        int vel = no.value("velocity").toInt(100);
        Note note(TimePos(len), TimePos(start), key, static_cast<volume_t>(vel));
        midiClip->addNote(note, false);
    }
    result.success = true; result.output = QString("%1 notes written").arg(notes.size());
    return result;
}

AiToolResult AiSidebar::executeAddEffectTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "add_effect"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const QString effectName = params.value("effect_name").toString();
    if (effectName.isEmpty()) { result.output = "Missing effect_name"; return result; }

    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    if (!targetTrack) { result.output = "Track not found"; return result; }

    AudioBusHandle* bus = nullptr;
    if (auto* it = dynamic_cast<InstrumentTrack*>(targetTrack)) bus = it->audioBusHandle();
    else if (auto* st = dynamic_cast<SampleTrack*>(targetTrack)) bus = st->audioBusHandle();
    if (!bus || !bus->effects()) { result.output = "No effect chain"; return result; }

    Effect* fx = Effect::instantiate(effectName, bus->effects(), nullptr);
    if (!fx) { result.output = "Failed to instantiate effect"; return result; }
    bus->effects()->appendEffect(fx);
    result.success = true; result.output = QString("Effect '%1' added").arg(effectName);
    return result;
}

AiToolResult AiSidebar::executeAddSampleClipTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "add_sample_clip"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const QString file = params.value("file").toString();
    const int startTicks = params.value("start_ticks").toInt(0);
    if (file.isEmpty()) { result.output = "Missing file"; return result; }

    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    auto* st = dynamic_cast<SampleTrack*>(targetTrack);
    if (!st) { result.output = "Target track is not a sample track"; return result; }

    auto* clip = dynamic_cast<SampleClip*>(st->createClip(TimePos(startTicks)));
    if (!clip) { result.output = "Failed to create sample clip"; return result; }
    clip->setSampleFile(file);
    result.success = true; result.output = QString("Sample clip added: %1").arg(QFileInfo(file).fileName());
    return result;
}

AiToolResult AiSidebar::executeCreateTrackTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "create_track"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString type = params.value("type").toString(); // "instrument" or "sample"
    const QString name = params.value("name").toString("New Track");
    Track* track = nullptr;
    if (type == "instrument") {
        track = Track::create(Track::Type::Instrument, song);
        if (auto* it = dynamic_cast<InstrumentTrack*>(track)) {
            const QString instrument = params.value("instrument").toString();
            if (!instrument.isEmpty()) { it->loadInstrument(instrument); }
            it->setName(name);
        }
    } else if (type == "sample") {
        track = Track::create(Track::Type::Sample, song);
        if (track) track->setName(name);
    } else {
        result.output = QString("Unknown track type '%1'. Valid types: 'instrument', 'sample'. Received params: %2").arg(type, QJsonDocument(params).toJson(QJsonDocument::Compact)); 
        return result;
    }
    if (!track) { result.output = "Failed to create track"; return result; }
    
    // Debug: Verify track was added and named correctly
    qDebug() << "CREATE_TRACK: Track created with name:" << track->name();
    qDebug() << "All tracks after creation:";
    for (Track* t : song->tracks()) { 
        qDebug() << "  - Track name:" << t->name() << "Type:" << (int)t->type();
    }
    
    result.success = true; result.output = QString("Created %1 track '%2'").arg(type, name);
    return result;
}

AiToolResult AiSidebar::executeMoveClipTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "move_clip"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int clipIndex = params.value("clip_index").toInt(0);
    const int newStart = params.value("start_ticks").toInt(0);
    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    if (!targetTrack) { result.output = "Track not found"; return result; }
    auto& clips = targetTrack->getClips();
    if (clipIndex < 0 || static_cast<size_t>(clipIndex) >= clips.size()) { result.output = "Clip index out of range"; return result; }
    Clip* clip = clips[clipIndex];
    clip->movePosition(TimePos(newStart));
    result.success = true; result.output = QString("Clip moved to %1").arg(newStart);
    return result;
}

AiToolResult AiSidebar::executeCreateAutomationClipTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "create_automation_clip"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const int start = params.value("start_ticks").toInt(0);
    // Find or create automation track by scanning tracks for type Automation
    Track* autoTrack = nullptr;
    for (Track* t : song->tracks()) { if (t->type() == Track::Type::Automation) { autoTrack = t; break; } }
    if (!autoTrack) { autoTrack = Track::create(Track::Type::Automation, song); }
    if (!autoTrack) { result.output = "Failed to access automation track"; return result; }
    auto* clip = dynamic_cast<AutomationClip*>(autoTrack->createClip(TimePos(start)));
    if (!clip) { result.output = "Failed to create automation clip"; return result; }
    result.success = true; result.output = QString("Automation clip created at %1").arg(start);
    return result;
}

AiToolResult AiSidebar::executeCreateSectionTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "create_section"; result.success = false;
    const QString name = params.value("name").toString();
    const int start = params.value("start_ticks").toInt(0);
    const int length = params.value("length_ticks").toInt(TimePos::ticksPerBar()*4);
    if (name.isEmpty() || length <= 0) { result.output = "Invalid name or length"; return result; }
    m_sections[name] = qMakePair(start, length);
    result.success = true; result.output = QString("Section '%1' registered at %2 len %3").arg(name).arg(start).arg(length);
    return result;
}

AiToolResult AiSidebar::executeDuplicateSectionTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "duplicate_section"; result.success = false;
    const QString name = params.value("name").toString();
    const int times = qMax(1, params.value("times").toInt(1));
    if (!m_sections.contains(name)) { result.output = "Section not found"; return result; }
    const auto sec = m_sections[name];
    const int start = sec.first; const int length = sec.second;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    for (Track* track : song->tracks()) {
        auto& clips = track->getClips();
        // Duplicate any clip overlapping [start, start+length)
        QList<Clip*> toDuplicate;
        for (Clip* c : clips) {
            if (!c) continue;
            const int cStart = c->startPosition();
            const int cEnd = c->endPosition();
            if (cStart < start + length && cEnd > start) {
                toDuplicate.append(c);
            }
        }
        for (Clip* base : toDuplicate) {
            const int baseOffset = qMax(0, start - (int)base->startPosition());
            const int baseLen = qMin((int)base->endPosition(), start + length) - qMax((int)base->startPosition(), start);
            for (int i = 0; i < times; ++i) {
                Clip* dup = base->clone(); if (!dup) { result.output = "Clone failed"; return result; }
                const int destStart = start + length * (i + 1) + ((int)base->startPosition() - start);
                dup->movePosition(TimePos(destStart));
                track->addClip(dup);
            }
        }
    }
    result.success = true; result.output = QString("Section '%1' duplicated %2x").arg(name).arg(times);
    return result;
}

AiToolResult AiSidebar::executeMutateSectionTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "mutate_section"; result.success = false;
    const QString name = params.value("name").toString();
    const QString mode = params.value("mode").toString("transpose"); // transpose|humanize|thin
    const int semis = params.value("semitones").toInt(0);
    if (!m_sections.contains(name)) { result.output = "Section not found"; return result; }
    const auto sec = m_sections[name]; const int start = sec.first; const int length = sec.second;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    int changed = 0;
    for (Track* track : song->tracks()) {
        if (auto* it = dynamic_cast<InstrumentTrack*>(track)) {
            for (Clip* clip : it->getClips()) {
                if (auto* midi = dynamic_cast<MidiClip*>(clip)) {
                    for (Note* n : midi->notes()) {
                        const int pos = n->pos();
                        if (pos >= start && pos < start + length) {
                            if (mode == "transpose") { n->setKey(qBound(0, n->key() + semis, 127)); changed++; }
                            else if (mode == "humanize") { n->setPos(TimePos(pos + (qrand()%7 - 3))); changed++; }
                            else if (mode == "thin") { if ((qrand()%3)==0) { n->setVolume(0); changed++; } }
                        }
                    }
                    midi->rearrangeAllNotes();
                }
            }
        }
    }
    result.success = true; result.output = QString("Mutated '%1' notes=%2 mode=%3").arg(name).arg(changed).arg(mode);
    return result;
}

AiToolResult AiSidebar::executeSidechainPumpAutomationTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "sidechain_pump_automation"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int start = params.value("start_ticks").toInt(0);
    const int bars = qMax(1, params.value("bars").toInt(4));
    const double depth = qBound(0.0, params.value("depth").toDouble(0.6), 1.0); // 0..1
    const double release = qBound(0.0, params.value("release").toDouble(0.5), 1.0); // 0..1 shaping

    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    auto* it = dynamic_cast<InstrumentTrack*>(targetTrack);
    if (!it) { result.output = "Instrument track not found"; return result; }

    // Create/get automation track
    Track* autoTrack = nullptr;
    for (Track* t : song->tracks()) { if (t->type() == Track::Type::Automation) { autoTrack = t; break; } }
    if (!autoTrack) { autoTrack = Track::create(Track::Type::Automation, song); }
    if (!autoTrack) { result.output = "Failed to access automation track"; return result; }

    // Create automation clip
    auto* clip = dynamic_cast<AutomationClip*>(autoTrack->createClip(TimePos(start)));
    if (!clip) { result.output = "Failed to create automation clip"; return result; }
    clip->clearObjects();
    // Target the instrument track's volume model
    if (!clip->addObject(it->volumeModel())) { result.output = "Failed to target volume"; return result; }

    const int ticksPerBar = TimePos::ticksPerBar();
    const int totalTicks = bars * ticksPerBar;
    const float minV = clip->getMin();
    const float maxV = clip->getMax();
    const float base = maxV; // normal level
    const float duck = maxV - static_cast<float>(depth) * (maxV - minV);

    // Program a 4-on-the-floor pump per bar
    for (int t = 0; t < totalTicks; t += ticksPerBar) {
        // At each quarter: dip then release
        for (int beat = 0; beat < 4; ++beat) {
            int beatStart = t + (ticksPerBar/4) * beat;
            clip->putValue(TimePos(beatStart), duck, true, true);
            int relTick = beatStart + static_cast<int>((ticksPerBar/4) * release);
            clip->putValue(TimePos(relTick), base, true, true);
        }
    }
    result.success = true; result.output = QString("Sidechain pump created on '%1' for %2 bars").arg(trackName).arg(bars);
    return result;
}

AiToolResult AiSidebar::executeQuantizeNotesTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "quantize_notes"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int clipIndex = params.value("clip_index").toInt(0);
    const QString gridStr = params.value("grid").toString("1/16");
    int divider = 16; // default 1/16
    if (gridStr == "1/8") divider = 8; else if (gridStr == "1/32") divider = 32; else if (gridStr == "1/4") divider = 4;
    const int qGrid = TimePos::ticksPerBar() / divider;

    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    auto* it = dynamic_cast<InstrumentTrack*>(targetTrack);
    if (!it) { result.output = "Instrument track not found"; return result; }
    auto& clips = it->getClips();
    if (clipIndex < 0 || static_cast<size_t>(clipIndex) >= clips.size()) { result.output = "Clip index out of range"; return result; }
    auto* midiClip = dynamic_cast<MidiClip*>(clips[clipIndex]);
    if (!midiClip) { result.output = "Target clip is not MIDI"; return result; }

    const auto& notes = midiClip->notes();
    for (Note* n : notes) {
        if (!n) continue;
        n->quantizePos(qGrid);
        n->quantizeLength(qGrid);
    }
    midiClip->rearrangeAllNotes();
    result.success = true; result.output = QString("Quantized notes to %1").arg(gridStr);
    return result;
}

AiToolResult AiSidebar::executeApplyGrooveTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "apply_groove"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int clipIndex = params.value("clip_index").toInt(0);
    const double swing = params.value("swing").toDouble(0.1); // 0..0.5 typical
    const int resolution = params.value("resolution").toInt(8); // subdivisions per bar for swing pairs

    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    auto* it = dynamic_cast<InstrumentTrack*>(targetTrack);
    if (!it) { result.output = "Instrument track not found"; return result; }
    auto& clips = it->getClips();
    if (clipIndex < 0 || static_cast<size_t>(clipIndex) >= clips.size()) { result.output = "Clip index out of range"; return result; }
    auto* midiClip = dynamic_cast<MidiClip*>(clips[clipIndex]);
    if (!midiClip) { result.output = "Target clip is not MIDI"; return result; }

    const int unit = TimePos::ticksPerBar() / resolution; // e.g., 8 -> 1/8 notes
    const int swingOffset = static_cast<int>(unit * swing);

    for (Note* n : midiClip->notes()) {
        if (!n) continue;
        int pos = n->pos();
        int indexInGrid = (pos / unit);
        if (indexInGrid % 2 == 1) {
            // push off-beat later for swing
            n->setPos(TimePos(pos + swingOffset));
        }
    }
    midiClip->rearrangeAllNotes();
    result.success = true; result.output = QString("Applied groove swing=%1 at res %2").arg(swing).arg(resolution);
    return result;
}

AiToolResult AiSidebar::executeDuplicateClipTool(const QJsonObject& params)
{
    AiToolResult result; result.toolName = "duplicate_clip"; result.success = false;
    Song* song = Engine::getSong(); if (!song) { result.output = "No project"; return result; }
    const QString trackName = params.value("track_name").toString();
    const int clipIndex = params.value("clip_index").toInt(0);
    const int times = qMax(1, params.value("times").toInt(1));

    Track* targetTrack = nullptr; for (Track* t : song->tracks()) { if (t->name() == trackName) { targetTrack = t; break; } }
    if (!targetTrack) { result.output = "Track not found"; return result; }
    auto& clips = targetTrack->getClips();
    if (clipIndex < 0 || static_cast<size_t>(clipIndex) >= clips.size()) { result.output = "Clip index out of range"; return result; }
    Clip* base = clips[clipIndex];
    const int len = base->length();
    TimePos nextPos = base->endPosition();
    for (int i = 0; i < times; ++i) {
        Clip* dup = base->clone();
        if (!dup) { result.output = "Failed to clone clip"; return result; }
        dup->movePosition(nextPos);
        targetTrack->addClip(dup);
        nextPos = nextPos + len;
    }
    result.success = true; result.output = QString("Duplicated clip %1 times").arg(times);
    return result;
}

AiToolResult AiSidebar::runTool(const QString& toolName, const QJsonObject& params)
{
    if (toolName == "read_project") return executeReadProjectTool(params);
    if (toolName == "modify_track") return executeModifyTrackTool(params);
    if (toolName == "add_instrument") return executeAddInstrumentTool(params);
    if (toolName == "analyze_audio") return executeAnalyzeAudioTool(params);
    if (toolName == "generate_pattern") return executeGeneratePatternTool(params);
    if (toolName == "mixer_control") return executeMixerControlTool(params);
    if (toolName == "export_project") return executeExportProjectTool(params);
    if (toolName == "search_plugin") return executeSearchPluginTool(params);
    if (toolName == "set_tempo") return executeSetTempoTool(params);
    if (toolName == "create_midi_clip") return executeCreateMidiClipTool(params);
    if (toolName == "write_notes") return executeWriteNotesTool(params);
    if (toolName == "add_effect") return executeAddEffectTool(params);
    if (toolName == "add_sample_clip") return executeAddSampleClipTool(params);
    if (toolName == "create_track") return executeCreateTrackTool(params);
    if (toolName == "move_clip") return executeMoveClipTool(params);
    if (toolName == "create_automation_clip") return executeCreateAutomationClipTool(params);
    AiToolResult r; r.toolName = toolName; r.success = false; r.output = "Unknown tool"; return r;
}

// AiSidebarController Implementation
AiSidebarController& AiSidebarController::instance()
{
    static AiSidebarController instance;
    return instance;
}

void AiSidebarController::initializeSidebar(QWidget* parent)
{
    if (!m_sidebar) {
        m_sidebar = new AiSidebar(parent);
        m_sidebar->move(parent->width() - m_sidebar->width(), 0);
        m_sidebar->resize(m_sidebar->width(), parent->height());
    }
}

void AiSidebarController::analyzeCurrentProject()
{
    if (m_sidebar) {
        // Trigger project analysis
        m_sidebar->sendMessage("Analyze the current project and suggest improvements");
    }
}

void AiSidebarController::suggestImprovements()
{
    if (m_sidebar) {
        m_sidebar->sendMessage("What improvements can be made to the mix and arrangement?");
    }
}

void AiSidebarController::generateFromPrompt(const QString& prompt)
{
    if (m_sidebar) {
        m_sidebar->sendMessage(prompt);
    }
}

} // namespace lmms::gui