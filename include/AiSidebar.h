#ifndef AI_SIDEBAR_H
#define AI_SIDEBAR_H

#include <QWidget>
#include <QNetworkAccessManager>
#include <QJsonObject>
#include <QJsonArray>
#include <memory>
#include <vector>
#include <functional>
#include <QMap>
#include <QPair>

#include "AiAgent.h"

QT_BEGIN_NAMESPACE
class QTextEdit;
class QLineEdit;
class QPushButton;
class QVBoxLayout;
class QScrollArea;
class QPropertyAnimation;
class QGraphicsOpacityEffect;
class QNetworkReply;
QT_END_NAMESPACE

namespace lmms::gui
{

class AiMessage : public QWidget
{
    Q_OBJECT
public:
    enum Role { User, Assistant, System };
    
    AiMessage(const QString& content, Role role, QWidget* parent = nullptr);
    void animateIn();
    
private:
    void setupUI();
    QString m_content;
    Role m_role;
    QGraphicsOpacityEffect* m_opacityEffect;
};

class AiToolResult
{
public:
    QString toolName;
    QJsonObject input;
    QString output;
    bool success;
};

class AiSidebar : public QWidget
{
    Q_OBJECT

public:
    explicit AiSidebar(QWidget* parent = nullptr);
    ~AiSidebar();

    void toggleVisibility();
    void setApiKey(const QString& key);
    void sendMessage(const QString& message);
    // Expose a synchronous tool runner for AiAgent
    AiToolResult runTool(const QString& toolName, const QJsonObject& params);
    
signals:
    void visibilityChanged(bool visible);
    void toolExecutionRequested(const QString& tool, const QJsonObject& params);

private slots:
    void onSendMessage();
    void onNetworkReply();
    void onTypingAnimation();
    void onToolExecutionComplete(const AiToolResult& result);
    
private:
    void setupUI();
    void setupAnimations();
    void sendToGPT5(const QString& message);
    void processGPT5Response(const QJsonObject& response);
    void executeToolCall(const QJsonObject& toolCall);
    void addMessage(const QString& content, AiMessage::Role role);
    void showTypingIndicator();
    void hideTypingIndicator();
    
    // Tool implementations
    AiToolResult executeReadProjectTool(const QJsonObject& params);
    AiToolResult executeModifyTrackTool(const QJsonObject& params);
    AiToolResult executeAddInstrumentTool(const QJsonObject& params);
    AiToolResult executeAnalyzeAudioTool(const QJsonObject& params);
    AiToolResult executeGeneratePatternTool(const QJsonObject& params);
    AiToolResult executeMixerControlTool(const QJsonObject& params);
    AiToolResult executeExportProjectTool(const QJsonObject& params);
    AiToolResult executeSearchPluginTool(const QJsonObject& params);
    // New concrete tools for end-to-end creation
    AiToolResult executeSetTempoTool(const QJsonObject& params);
    AiToolResult executeCreateMidiClipTool(const QJsonObject& params);
    AiToolResult executeWriteNotesTool(const QJsonObject& params);
    AiToolResult executeAddEffectTool(const QJsonObject& params);
    AiToolResult executeAddSampleClipTool(const QJsonObject& params);
    AiToolResult executeCreateTrackTool(const QJsonObject& params);
    AiToolResult executeMoveClipTool(const QJsonObject& params);
    // Arrangement / Automation / Quantize / Groove (minimal implementations)
    AiToolResult executeCreateAutomationClipTool(const QJsonObject& params);
    AiToolResult executeCreateSectionTool(const QJsonObject& params);
    AiToolResult executeDuplicateSectionTool(const QJsonObject& params);
    AiToolResult executeMutateSectionTool(const QJsonObject& params);
    AiToolResult executeSidechainPumpAutomationTool(const QJsonObject& params);
    AiToolResult executeQuantizeNotesTool(const QJsonObject& params);
    AiToolResult executeApplyGrooveTool(const QJsonObject& params);
    AiToolResult executeDuplicateClipTool(const QJsonObject& params);
    
    // UI Components
    QScrollArea* m_scrollArea;
    QWidget* m_messagesContainer;
    QVBoxLayout* m_messagesLayout;
    QLineEdit* m_inputField;
    QPushButton* m_sendButton;
    QWidget* m_typingIndicator;
    QPropertyAnimation* m_slideAnimation;
    QPropertyAnimation* m_fadeAnimation;
    
    // Network
    std::unique_ptr<QNetworkAccessManager> m_networkManager;
    QNetworkReply* m_currentReply;
    
    // State
    QString m_apiKey;
    QJsonArray m_conversationHistory;
    bool m_isProcessing;
    QString m_previousResponseId;  // For GPT-5 reasoning context
    
    // AI Agent for intelligent orchestration
    std::unique_ptr<AiAgent> m_aiAgent;
    
    // GPT-5 specific settings
    struct GPT5Settings {
        QString model = "gpt-5";
        QString reasoningEffort = "medium";
        QString verbosity = "medium";
        bool usePreambles = true;
        int maxTokens = 4096;
        QJsonArray allowedTools;
    } m_gpt5Settings;
    
    // Tool definitions for GPT-5
    QJsonArray getToolDefinitions() const;

    // Arrangement section registry (name -> <startTicks,lengthTicks>)
    QMap<QString, QPair<int,int>> m_sections;
};

class AiSidebarController : public QObject
{
    Q_OBJECT
    
public:
    static AiSidebarController& instance();
    
    void initializeSidebar(QWidget* parent);
    AiSidebar* sidebar() const { return m_sidebar; }
    
    // Project-wide tool capabilities
    void analyzeCurrentProject();
    void suggestImprovements();
    void generateFromPrompt(const QString& prompt);
    
private:
    AiSidebarController() = default;
    AiSidebar* m_sidebar = nullptr;
};

} // namespace lmms::gui

#endif // AI_SIDEBAR_H