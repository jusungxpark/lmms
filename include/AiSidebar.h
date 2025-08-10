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
#include "AudioAnalyzer.h"

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
    void onActionButtonClicked();

private:
    // UI
    void setupUI();
    void addMessage(const QString& text, const QString& role);
    void addMessageWithActions(const QString& text, const QString& role, const QStringList& actions);

    // GPT-5 request
    void sendToGPT5(const QString& message);
    bool processResponse(const QJsonObject& response);

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
    
    // Comprehensive inspection and analysis tools
    AiToolResult toolInspectTrack(const QJsonObject& p);
    AiToolResult toolGetTrackNotes(const QJsonObject& p);
    AiToolResult toolModifyNotes(const QJsonObject& p);
    AiToolResult toolAnalyzeBeforeWriting(const QJsonObject& p);
    
    // Effect management tools
    AiToolResult toolListEffects(const QJsonObject& p);
    AiToolResult toolConfigureEffect(const QJsonObject& p);
    AiToolResult toolRemoveEffect(const QJsonObject& p);
    
    // Autonomous and self-testing tools
    AiToolResult toolAutonomousCompose(const QJsonObject& p);
    AiToolResult toolRunSelfTest(const QJsonObject& p);
    
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
    
    // ========= COMPREHENSIVE MIXING & ANALYSIS TOOLS =========
    AiToolResult toolBalanceTrackVolumes(const QJsonObject& p);
    AiToolResult toolCreateFullProduction(const QJsonObject& p);

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
    
    // Context-aware AI decision making
    QJsonObject analyzeProjectContext() const;
    QJsonObject makeIntelligentParameters(const QString& trackType, const QJsonObject& context) const;
    QString selectComplementaryInstrument(const QString& trackType, const QJsonObject& context) const;
    
    // Helpers
    InstrumentTrack* findInstrumentTrack(const QString& name) const;
    Track* findTrack(const QString& name) const;
    void initializeAgents();
    void setupSafetyGuards();
    void loadApiKeyFromEnv();
    void executeApprovedPlan(const QString& originalRequest);
    
    // Autonomous execution functions
    void executeAutonomousAction(const QString& planText);
    void createFullArrangement(const QString& style);
    void validateAndFixAllTracks(); // Iterative validation system
    void createDrumTrack();
    void createBassTrack();
    void createChordTrack();
    void createLeadTrack();
    void createPadTrack();
    
    // Creative music generation functions
    void createDrumTrackCreative(const QString& style, int bpm);
    void createBassTrackCreative(const QString& key, const QString& scale, const QString& progression);
    void createChordTrackCreative(const QString& key, const QString& progression);
    void createLeadTrackCreative(const QString& key, const QString& scale);
    void createPadTrackCreative(const QString& key, const QString& progression);
    void applySidechainWithVariation();
    void createDynamicArrangementStructure();
    
    // Professional multi-track production
    void createProfessionalArrangement(const QString& userRequest);
    void createProfessionalDrums(int genre);
    void createProfessionalBass(int genre, const QString& key, const QString& progression);
    void createProfessionalMelodic(int genre, const QString& key, const QString& scale, const QString& progression);
    void createProfessionalFX(int genre);
    void applyProfessionalMixing(int genre);
    

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
    
    // Pending actions for approval workflow
    QString m_pendingUserRequest;
    QJsonObject m_pendingActionPlan;
    
    // Current user input for autonomous execution
    QString m_currentUserInput;
    
    // Audio feedback system
    std::unique_ptr<AudioListener> m_audioListener;
    bool m_audioFeedbackEnabled {true};
    
    // Get audio feedback for AI decisions
    QJsonObject getAudioFeedback() const;
    void updateFromAudioFeedback(const QJsonObject& feedback);
};

} // namespace lmms::gui

#endif
