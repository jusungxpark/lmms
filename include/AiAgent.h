#ifndef AI_AGENT_H
#define AI_AGENT_H

#include <QObject>
#include <QJsonObject>
#include <QJsonArray>
#include <QString>
#include <QTimer>
#include <QStringList>
#include <functional>

namespace lmms::gui
{

// Forward declarations
class AiSidebar;
class AiToolResult;

// Musical knowledge structures
struct MusicalPattern {
    QString genre;
    int tempo;
    QString timeSignature;
    QStringList scaleNotes;
    QStringList chordProgression;
    QJsonObject drumPattern;
    QJsonObject rhythmicStructure;
};

struct ToolCapability {
    QString name;
    QStringList requirements;
    QStringList effects;
    int complexity;
    double executionTime;
    QStringList dependencies;
};

// Enhanced tool execution context
struct ExecutionContext {
    QString sessionId;
    QJsonObject projectState;
    QStringList availableTracks;
    QStringList availableInstruments;
    QStringList recentActions;
    QJsonObject musicalContext;
    int errorCount;
    QString currentGoal;
};

// AI Agent orchestration and planning system
class AiAgent : public QObject
{
    Q_OBJECT

public:
    explicit AiAgent(AiSidebar* sidebar, QObject* parent = nullptr);
    
    // Main agent interface
    void processUserIntent(const QString& userMessage);
    void executeToolSequence(const QJsonArray& toolSequence);
    void handleToolResult(const AiToolResult& result);
    
    // Musical intelligence
    MusicalPattern analyzeMusicalStyle(const QString& style);
    QJsonArray generateBeatPattern(const MusicalPattern& pattern);
    QJsonArray createChordProgression(const QString& key, const QString& style);
    QJsonArray generateMelody(const MusicalPattern& pattern, const QJsonArray& chords);
    
    // Tool orchestration
    QJsonArray planToolSequence(const QString& goal, const QJsonObject& context);
    bool validateToolSequence(const QJsonArray& sequence);
    void optimizeToolExecution(QJsonArray& sequence);
    
    // State management
    void updateProjectState();
    QJsonObject getExecutionContext() const;
    void resetSession();
    
    // Error handling and recovery
    void handleExecutionError(const QString& error, const QString& toolName);
    QJsonArray suggestRecoveryActions(const QString& error);
    bool canRecoverFromError(const QString& error);
    
signals:
    void toolSequenceReady(const QJsonArray& sequence);
    void executionCompleted(bool success, const QString& summary);
    void errorRecoveryNeeded(const QString& error, const QJsonArray& suggestions);

private slots:
    void onExecutionTimer();
    void onStateUpdateTimer();

private:
    // Core agent functions
    void analyzeUserIntent(const QString& message);
    QJsonObject extractMusicalParameters(const QString& message);
    QStringList identifyRequiredTools(const QString& intent);
    void executeNextStep();
    
    // Intelligent analysis functions
    bool needsWebResearch(const QString& message);
    void performWebResearch(const QString& query);
    QJsonObject analyzeWithGPT5(const QString& message);
    void fallbackAnalysis(const QString& message);
    QJsonObject analyzeStyleCharacteristics(const QString& style, const QJsonObject& webData = QJsonObject());
    QJsonArray generateDynamicToolSequence(const QJsonObject& styleAnalysis);
    
    // AI-Native orchestration methods
    QJsonObject makeAIAPICall(const QString& message);
    QJsonObject makeAIAPICallWithRetry(const QString& message, int maxRetries = 3);
    QString getOpenAIAPIKey();
    QString getLMMSToolsDescription();
    QString getLMMSInstrumentsDescription();
    QJsonObject processAIOrchestrationResponse(const QJsonObject& aiResponse);
    
    // Legacy methods (to be removed)
    QJsonObject performAdvancedAIReasoning(const QString& message);
    QJsonObject analyzeMusicalSemantics(const QString& message);
    QJsonObject generateAIPatterns(const QJsonObject& analysis);
    
    // Semantic analysis helpers
    QString inferGenreFromSemantics(const QString& text, const QString& mood);
    QString inferRhythmStyle(const QString& genre, const QString& mood);
    QString inferHarmonyType(const QString& genre, const QString& mood);
    QString inferSoundDesign(const QString& genre, const QString& mood);
    QString inferArrangement(const QString& genre, const QString& complexity);
    QString inferKeySignature(const QString& mood);
    QJsonArray generateAIInstrumentSelection(const QJsonObject& semantics);
    QString selectDrumPreset(const QString& genre, const QString& mood);
    QString selectBassPreset(const QString& genre, const QString& mood);
    QString selectLeadPreset(const QString& genre, const QString& mood);
    bool containsAny(const QString& text, const QStringList& words);
    
    // Supporting methods (legacy - will be removed)
    QJsonObject simulateWebResearch(const QString& searchTerm);
    QJsonObject simulateGPT5Analysis(const QString& message);
    QJsonObject analyzeGenreFromContext(const QString& lowerMsg);
    QJsonArray generateInstrumentRecommendations(const QJsonObject& analysis);
    
    // Dynamic sequence generation
    QJsonArray createBasicSequence(const QString& goal);
    QJsonArray generateMusicalContent(const QString& instrumentType, const QString& genre, const QString& role, int tempo);
    QJsonArray generateAIMusicalContent(const QString& instrumentType, const QJsonObject& aiAnalysis);
    QJsonArray generateAIDrumPattern(const QString& genre, const QString& mood, int tempo, const QJsonObject& styleChar);
    QJsonArray generateAIBassPattern(const QString& genre, const QString& mood, int tempo, const QJsonObject& styleChar);
    QJsonArray generateAIChordPattern(const QString& genre, const QString& mood, const QString& key, const QJsonObject& styleChar);
    QJsonArray generateAIMelodyPattern(const QString& genre, const QString& mood, int tempo, const QString& key, const QJsonObject& styleChar);
    QJsonArray generateDrumPattern(const QString& genre, int tempo);
    QJsonArray generateBassPattern(const QString& genre, int tempo);
    QJsonArray generateChordPattern(const QString& genre);
    QJsonArray generateMelodyPattern(const QString& genre, int tempo);
    QJsonArray getEffectsForGenreAndInstrument(const QString& genre, const QString& instrument);
    QString capitalizeFirst(const QString& str);
    
    // Music theory engine
    void initializeMusicalKnowledge();
    QStringList getScaleNotes(const QString& key, const QString& scale);
    QJsonArray getChordNotes(const QString& chord, const QString& key);
    int getBPMForGenre(const QString& genre);
    QStringList getTypicalInstruments(const QString& genre);
    
    // Tool intelligence
    void initializeToolCapabilities();
    bool areToolsCompatible(const QString& tool1, const QString& tool2);
    QStringList getToolDependencies(const QString& toolName);
    double estimateExecutionTime(const QJsonArray& toolSequence);
    
    // Execution planning
    QJsonArray createMinimalViableSequence(const QString& goal);
    QJsonArray expandSequenceForQuality(const QJsonArray& baseSequence);
    void addValidationSteps(QJsonArray& sequence);
    
    // Hallucination prevention
    bool validateParameters(const QJsonObject& params, const QString& toolName);
    bool isReasonableValue(const QString& parameter, const QVariant& value);
    QJsonObject sanitizeParameters(const QJsonObject& params, const QString& toolName);
    
    // State tracking
    void updateMusicalContext(const AiToolResult& result);
    void trackToolUsage(const QString& toolName, bool success);
    QJsonObject getProjectAnalysis() const;
    
    AiSidebar* m_sidebar;
    ExecutionContext m_context;
    
    // Musical knowledge base
    QJsonObject m_musicalStyles;
    QJsonObject m_scaleDatabase;
    QJsonObject m_chordDatabase;
    QJsonObject m_rhythmPatterns;
    QJsonObject m_genreTemplates;
    
    // Tool capabilities
    QHash<QString, ToolCapability> m_toolCapabilities;
    QJsonObject m_toolCompatibility;
    QStringList m_criticalTools;
    
    // Execution state
    QTimer* m_executionTimer;
    QTimer* m_stateUpdateTimer;
    QString m_currentSessionId;
    QJsonArray m_currentSequence;
    int m_currentStepIndex;
    int m_maxRetries;
    
    // Error tracking
    QHash<QString, int> m_errorHistory;
    QStringList m_recentErrors;
    QJsonObject m_recoveryStrategies;
};

// Comprehensive tool definitions for GPT-5
class MusicProductionTools
{
public:
    static QJsonArray getComprehensiveToolDefinitions();
    
private:
    static QJsonObject createCompositionTools();
    static QJsonObject createArrangementTools();
    static QJsonObject createAudioTools();
    static QJsonObject createInstrumentTools();
    static QJsonObject createMixingTools();
    static QJsonObject createWorkflowTools();
    static QJsonObject createAnalysisTools();
    static QJsonObject createEffectsTools();
    static QJsonObject createAutomationTools();
    static QJsonObject createPerformanceTools();
};

// Musical pattern generator
class PatternGenerator 
{
public:
    // Drum patterns
    static QJsonArray generateHouseKick();
    static QJsonArray generateTrapHiHats();
    static QJsonArray generateBreakbeat();
    static QJsonArray generateFredAgainStylePattern();
    
    // Melodic patterns  
    static QJsonArray generateBassline(const QString& key, const QString& style);
    static QJsonArray generateArpeggio(const QStringList& chordNotes);
    static QJsonArray generateMelodic(const QString& key, const QString& scale);
    
    // Chord progressions
    static QJsonArray getPopularProgression(const QString& key);
    static QJsonArray getGenreProgression(const QString& genre, const QString& key);
    
private:
    static QJsonArray scaleToMidiNotes(const QStringList& scale, int octave);
    static int noteToMidi(const QString& note, int octave);
};

} // namespace lmms::gui

#endif // AI_AGENT_H