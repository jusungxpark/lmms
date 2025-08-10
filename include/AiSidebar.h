/*
 * AiSidebar.h - minimal GPT-5 tool layer and sidebar UI
 */

#ifndef LMMS_GUI_AI_SIDEBAR_H
#define LMMS_GUI_AI_SIDEBAR_H

#include "SideBarWidget.h"
#include <QJsonObject>
#include <QJsonArray>
#include <QHash>
#include <QTimer>
#include <memory>

QT_BEGIN_NAMESPACE
class QVBoxLayout;
class QScrollArea;
class QLineEdit;
class QPushButton;
class QNetworkAccessManager;
class QNetworkReply;
class QProgressBar;
class QLabel;
QT_END_NAMESPACE

namespace lmms {
class Song;
class Track;
class InstrumentTrack;
class SampleTrack;
class MidiClip;
class AutomationClip;
}

namespace lmms::gui {

// Symbolic project representation (Architecture principle #1)
struct ProjectSnapshot {
    QString hash;
    QJsonObject session;
    QJsonArray tracks;
    QJsonArray regions;
    QJsonObject mixGraph;
    qint64 timestamp;
};

struct ChangeOperation {
    QString id;
    QString type; // "midi_patch", "track_create", "automation_apply", etc.
    QJsonObject target;
    QJsonObject changes;
    QJsonObject rollback;
    QString hash; // Content hash for safety
};

struct AiToolResult {
    QString toolName;
    QJsonObject input;
    QString output;
    bool success {false};
    QList<ChangeOperation> operations; // For undo/diff tracking
    QString previewId; // For A/B comparison
};

// Multi-agent types (Architecture principle #3)
enum class AgentRole {
    Planner,
    Composer,
    SoundDesigner, 
    RhythmGroove,
    MixAssistant,
    Critic
};

class AiSidebar : public SideBarWidget {
    Q_OBJECT
public:
    explicit AiSidebar(QWidget* parent = nullptr);
    ~AiSidebar() override;

private slots:
    void onSend();
    void onNetworkFinished();

private:
    // UI
    void setupUI();
    void addMessage(const QString& text, const QString& role);

    // GPT-5 request
    void sendToGPT5(const QString& message);
    void processResponse(const QJsonObject& response);

    // Tool registry and execution
    QJsonArray getToolDefinitions() const;
    void executeToolCall(const QJsonObject& toolCall);

    // Core DAW tools
    AiToolResult toolSetTempo(const QJsonObject& p);
    AiToolResult toolSetTimeSignature(const QJsonObject& p);
    AiToolResult toolCreateTrack(const QJsonObject& p);
    AiToolResult toolCreateMidiClip(const QJsonObject& p);
    AiToolResult toolWriteNotes(const QJsonObject& p);
    AiToolResult toolQuantizeTrack(const QJsonObject& p);
    AiToolResult toolApplyGroove(const QJsonObject& p);
    AiToolResult toolAddEffect(const QJsonObject& p);
    AiToolResult toolAddSampleClip(const QJsonObject& p);
    AiToolResult toolCreateAutomationClip(const QJsonObject& p);
    AiToolResult toolExportProject(const QJsonObject& p);
    
    // Advanced composition tools
    AiToolResult toolCreateSongSection(const QJsonObject& p);
    AiToolResult toolDuplicateSection(const QJsonObject& p);
    AiToolResult toolMutatePattern(const QJsonObject& p);
    AiToolResult toolCreateChordProgression(const QJsonObject& p);
    AiToolResult toolCreateMelody(const QJsonObject& p);
    AiToolResult toolCreateDrumPattern(const QJsonObject& p);
    
    // Advanced automation & effects
    AiToolResult toolCreateSidechainPump(const QJsonObject& p);
    AiToolResult toolCreateFilterSweep(const QJsonObject& p);
    AiToolResult toolCreateVolumeAutomation(const QJsonObject& p);
    AiToolResult toolCreateSendBus(const QJsonObject& p);
    
    // Workflow tools
    AiToolResult toolAnalyzeProject(const QJsonObject& p);
    AiToolResult toolSuggestImprovements(const QJsonObject& p);
    AiToolResult toolCreateUndo(const QJsonObject& p);
    AiToolResult toolPreviewChanges(const QJsonObject& p);
    AiToolResult toolExportAudio(const QJsonObject& p);

    // Symbolic reasoning (Architecture principle #1)
    ProjectSnapshot captureSnapshot() const;
    QJsonObject analyzeProject() const;
    QJsonObject detectChords(const QStringList& trackNames = {}) const;
    QJsonObject detectKeyAndTempo() const;
    QString computeContentHash(const QJsonObject& content) const;
    
    // Multi-agent orchestration (Architecture principle #3)
    void switchAgent(AgentRole role, const QJsonObject& context = {});
    QJsonObject plannerAgent(const QString& request);
    QJsonObject composerAgent(const QJsonObject& task);
    QJsonObject mixAssistantAgent(const QJsonObject& task);
    QJsonObject criticAgent(const QJsonObject& changes);
    
    // Change management with diffs (Architecture principle #5)
    QString createSnapshot(const QString& label = "");
    bool applyChanges(const QList<ChangeOperation>& ops);
    bool revertToSnapshot(const QString& snapshotId);
    QJsonObject generateDiff(const QString& fromSnapshot, const QString& toSnapshot) const;
    
    // Preview system (Cursor-like)
    QString generatePreview(const QList<ChangeOperation>& ops);
    void showDiffView(const QJsonObject& diff);
    bool runSafetyChecks(const QList<ChangeOperation>& ops) const;
    
    // Natural language processing
    QJsonObject parseMusicalIntent(const QString& request);
    
    // Helpers
    InstrumentTrack* findInstrumentTrack(const QString& name) const;
    Track* findTrack(const QString& name) const;
    void initializeAgents();
    void setupSafetyGuards();
    void loadApiKeyFromEnv();
    

private:
    QVBoxLayout* m_rootLayout {nullptr};
    QScrollArea* m_scroll {nullptr};
    QWidget* m_msgs {nullptr};
    QVBoxLayout* m_msgsLayout {nullptr};
    QLineEdit* m_input {nullptr};
    QPushButton* m_send {nullptr};
    QProgressBar* m_progressBar {nullptr};
    QLabel* m_statusLabel {nullptr};
    
    // Processing state
    enum class ProcessingState {
        Idle,
        SendingRequest,
        WaitingResponse,
        ExecutingTools,
        Error
    };
    ProcessingState m_state {ProcessingState::Idle};
    
    // UI state management
    void setState(ProcessingState state);
    void executeDirectAction();

    std::unique_ptr<QNetworkAccessManager> m_net;
    QNetworkReply* m_reply {nullptr};
    QJsonArray m_history; // chat-style messages
    QString m_apiKey;
    
    // Retry logic for API calls
    int m_retryCount {0};
    int m_maxRetries {5};
    QString m_lastMessage;
    
    // Symbolic-first architecture state
    QHash<QString, ProjectSnapshot> m_snapshots; // Version control
    QList<ChangeOperation> m_pendingChanges;
    QJsonObject m_projectAnalysis; // Cached symbolic analysis
    QString m_currentSnapshotId;
    
    // Multi-agent state
    AgentRole m_currentAgent {AgentRole::Planner};
    QJsonObject m_agentContext;
    
    // Preview and diff system
    QString m_previewId;
    QHash<QString, QByteArray> m_audioPreviews;
    bool m_previewMode {false};
    
    // Safety and guardrails
    QTimer* m_safetyTimer;
    QJsonObject m_styleInvariants; // Tempo, key constraints
};

} // namespace lmms::gui

#endif


