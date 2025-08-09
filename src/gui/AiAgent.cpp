#include "AiAgent.h"
#include "AiSidebar.h"
#include "Song.h"
#include "Engine.h"
#include "Track.h"
#include "InstrumentTrack.h"
#include "TimePos.h"
#include "Note.h"

#include <QJsonDocument>
#include <QDebug>
#include <QUuid>
#include <QtMath>
#include <QRegularExpression>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QUrl>
#include <QUrlQuery>
#include <QEventLoop>
#include <QFile>
#include <QTextStream>
#include <QTimer>

namespace lmms::gui
{

AiAgent::AiAgent(AiSidebar* sidebar, QObject* parent)
    : QObject(parent)
    , m_sidebar(sidebar)
    , m_currentStepIndex(0)
    , m_maxRetries(3)
{
    // Initialize timers
    m_executionTimer = new QTimer(this);
    m_executionTimer->setSingleShot(true);
    connect(m_executionTimer, &QTimer::timeout, this, &AiAgent::onExecutionTimer);
    
    m_stateUpdateTimer = new QTimer(this);
    m_stateUpdateTimer->setInterval(1000); // Update state every second
    connect(m_stateUpdateTimer, &QTimer::timeout, this, &AiAgent::onStateUpdateTimer);
    m_stateUpdateTimer->start();
    
    // Initialize knowledge bases
    initializeMusicalKnowledge();
    initializeToolCapabilities();
    
    // Initialize session
    resetSession();
    
    qDebug() << "AiAgent initialized with comprehensive music production intelligence";
}

void AiAgent::processUserIntent(const QString& userMessage)
{
    qDebug() << "=== AI-NATIVE INTENT PROCESSING ===";
    qDebug() << "User message:" << userMessage;
    
    updateProjectState();
    
    // Use pure AI orchestration - no hardcoded logic
    QJsonObject aiOrchestration = analyzeWithGPT5(userMessage);
    
    if (aiOrchestration.contains("error")) {
        QString errorMsg = aiOrchestration["message"].toString();
        qDebug() << "AI orchestration error:" << errorMsg;
        emit executionCompleted(false, errorMsg);
        return;
    }
    
    if (aiOrchestration.contains("tool_sequence")) {
        // AI successfully created tool sequence
        QJsonArray toolSequence = aiOrchestration["tool_sequence"].toArray();
        QJsonObject analysis = aiOrchestration["analysis"].toObject();
        
        // Update context with AI analysis
        m_context.musicalContext = analysis;
        m_context.currentGoal = analysis["musical_style"].toString();
        
        qDebug() << "AI generated" << toolSequence.size() << "tool steps";
        qDebug() << "Expected outcome:" << aiOrchestration["expected_outcome"].toString();
        
        if (!toolSequence.isEmpty()) {
            emit toolSequenceReady(toolSequence);
            executeToolSequence(toolSequence);
        } else {
            emit executionCompleted(false, "AI generated empty tool sequence");
        }
    } else {
        qDebug() << "AI orchestration did not produce tool sequence";
        emit executionCompleted(false, "AI orchestration failed to create execution plan");
    }
}

void AiAgent::analyzeUserIntent(const QString& message)
{
    // Use GPT-5 reasoning for intelligent musical style analysis
    qDebug() << "Analyzing user intent with AI reasoning:" << message;
    
    // First check if we need web search for unfamiliar references
    if (needsWebResearch(message)) {
        performWebResearch(message);
    }
    
    // Use GPT-5 to analyze the musical request
    QJsonObject aiAnalysis = analyzeWithGPT5(message);
    
    // Merge AI analysis into musical context
    if (!aiAnalysis.isEmpty()) {
        m_context.musicalContext = aiAnalysis;
        qDebug() << "AI Analysis complete:" << QJsonDocument(aiAnalysis).toJson(QJsonDocument::Compact);
    } else {
        qDebug() << "AI analysis failed, falling back to basic parsing";
        fallbackAnalysis(message);
    }
}

QJsonObject AiAgent::extractMusicalParameters(const QString& message)
{
    QJsonObject params;
    QString lowerMsg = message.toLower();
    
    // Tempo extraction
    QRegularExpression bpmRegex("(\\d+)\\s*bpm");
    QRegularExpressionMatch bpmMatch = bpmRegex.match(lowerMsg);
    if (bpmMatch.hasMatch()) {
        params["tempo"] = bpmMatch.captured(1).toInt();
    }
    
    // Key detection
    QStringList keys = {"c", "c#", "db", "d", "d#", "eb", "e", "f", "f#", "gb", "g", "g#", "ab", "a", "a#", "bb", "b"};
    for (const QString& key : keys) {
        if (lowerMsg.contains(key + " major") || lowerMsg.contains(key + " minor")) {
            params["key"] = key;
            params["scale"] = lowerMsg.contains("minor") ? "minor" : "major";
            break;
        }
    }
    
    // Time signature detection
    QRegularExpression timeSigRegex("(\\d+)/(\\d+)");
    QRegularExpressionMatch timeSigMatch = timeSigRegex.match(lowerMsg);
    if (timeSigMatch.hasMatch()) {
        params["time_signature"] = QString("%1/%2").arg(timeSigMatch.captured(1)).arg(timeSigMatch.captured(2));
    }
    
    // Length/bars detection
    QRegularExpression barsRegex("(\\d+)\\s*bar");
    QRegularExpressionMatch barsMatch = barsRegex.match(lowerMsg);
    if (barsMatch.hasMatch()) {
        params["length_bars"] = barsMatch.captured(1).toInt();
    }
    
    // Dynamic intent classification based on AI analysis
    QJsonObject aiContext = m_context.musicalContext;
    
    if (!aiContext.isEmpty()) {
        // Use AI-analyzed intent
        params["intent"] = aiContext["intent"].toString();
        params["complexity"] = aiContext["complexity"].toString();
        params["elements"] = aiContext["elements"].toArray();
        params["genre"] = aiContext["genre"].toString();
        params["style_characteristics"] = aiContext["style_characteristics"].toObject();
    } else {
        // Simple fallback for basic requests
        if (lowerMsg.contains("beat") || lowerMsg.contains("drum")) {
            params["intent"] = "create_drum_pattern";
            params["complexity"] = "medium";
        } else if (lowerMsg.contains("full") && (lowerMsg.contains("track") || lowerMsg.contains("song"))) {
            params["intent"] = "create_full_arrangement";
            params["complexity"] = "high";
        }
    }
    
    return params;
}

MusicalPattern AiAgent::analyzeMusicalStyle(const QString& style)
{
    MusicalPattern pattern;
    QString lowerStyle = style.toLower();
    
    // Load from knowledge base or create pattern
    if (lowerStyle == "fred again" || lowerStyle == "uk_garage") {
        pattern.genre = "uk_garage";
        pattern.tempo = 128;
        pattern.timeSignature = "4/4";
        pattern.scaleNotes = getScaleNotes("c", "major");
        pattern.chordProgression = QStringList({"vi", "IV", "I", "V"}); // Am-F-C-G in C major
        
        // Fred Again style drum pattern
        QJsonObject drumPattern;
        drumPattern["kick"] = QJsonArray{0, 32, 48}; // Syncopated kick pattern
        drumPattern["snare"] = QJsonArray{16, 48}; // Backbeat
        drumPattern["hihat"] = QJsonArray{8, 12, 24, 28, 40, 44, 56, 60}; // Swung hats
        drumPattern["swing"] = 0.15; // UK Garage swing
        pattern.drumPattern = drumPattern;
        
    } else if (lowerStyle == "house") {
        pattern.genre = "house";
        pattern.tempo = 126;
        pattern.timeSignature = "4/4";
        pattern.scaleNotes = getScaleNotes("f", "minor");
        pattern.chordProgression = QStringList({"i", "VII", "VI", "i"}); // Fm-Eb-Db-Fm
        
        QJsonObject drumPattern;
        drumPattern["kick"] = QJsonArray{0, 16, 32, 48}; // Four-on-floor
        drumPattern["hihat"] = QJsonArray{8, 24, 40, 56}; // Offbeat hats
        drumPattern["openhat"] = QJsonArray{32}; // Open hat accent
        pattern.drumPattern = drumPattern;
        
    } else if (lowerStyle == "trap") {
        pattern.genre = "trap";
        pattern.tempo = 140;
        pattern.timeSignature = "4/4";
        pattern.scaleNotes = getScaleNotes("d", "minor");
        pattern.chordProgression = QStringList({"i", "bVII", "i", "i"});
        
        QJsonObject drumPattern;
        drumPattern["kick"] = QJsonArray{0, 24, 48};
        drumPattern["snare"] = QJsonArray{16, 48};
        drumPattern["hihat"] = QJsonArray{4, 6, 8, 10, 12, 14, 20, 22, 28, 30, 36, 38, 44, 46, 52, 54, 60, 62}; // Trap rolls
        pattern.drumPattern = drumPattern;
    }
    
    return pattern;
}

QJsonArray AiAgent::planToolSequence(const QString& goal, const QJsonObject& context)
{
    qDebug() << "Planning dynamic tool sequence for goal:" << goal;
    qDebug() << "Context:" << QJsonDocument(context).toJson(QJsonDocument::Compact);
    
    // Use intelligent style analysis from the musical context
    QJsonObject musicalContext = m_context.musicalContext;
    
    if (musicalContext.isEmpty()) {
        qDebug() << "No musical context available, creating basic sequence";
        return createBasicSequence(goal);
    }
    
    // Generate dynamic sequence based on analyzed musical characteristics
    return generateDynamicToolSequence(musicalContext);
}

void AiAgent::executeToolSequence(const QJsonArray& toolSequence)
{
    m_currentSequence = toolSequence;
    m_currentStepIndex = 0;
    
    qDebug() << "Executing tool sequence with" << toolSequence.size() << "steps";
    
    if (!toolSequence.isEmpty()) {
        executeNextStep();
    } else {
        emit executionCompleted(false, "Empty tool sequence");
    }
}

void AiAgent::executeNextStep()
{
    if (m_currentStepIndex >= m_currentSequence.size()) {
        emit executionCompleted(true, "All tools executed successfully");
        return;
    }
    
    QJsonObject step = m_currentSequence[m_currentStepIndex].toObject();
    QString toolName = step["tool"].toString();
    QJsonObject params = step["params"].toObject();
    
    // Validate parameters before execution
    if (!validateParameters(params, toolName)) {
        params = sanitizeParameters(params, toolName);
    }
    
    qDebug() << "Executing step" << m_currentStepIndex << ":" << toolName;
    
    // Execute via sidebar (which has the actual tool implementations)
    if (m_sidebar) {
        // Call through the public runTool API and synthesize completion
        AiToolResult res = m_sidebar->runTool(toolName, params);
        handleToolResult(res);
    }
    
    // Start timeout timer - increased for complex operations like Fred Again beats
    m_executionTimer->start(30000); // 30 second timeout per tool
}

void AiAgent::handleToolResult(const AiToolResult& result)
{
    m_executionTimer->stop();
    
    // Track tool usage
    trackToolUsage(result.toolName, result.success);
    
    if (result.success) {
        updateMusicalContext(result);
        m_currentStepIndex++;
        
        // Short delay before next step
        QTimer::singleShot(100, this, &AiAgent::executeNextStep);
    } else {
        handleExecutionError(result.output, result.toolName);
    }
}

void AiAgent::handleExecutionError(const QString& error, const QString& toolName)
{
    m_context.errorCount++;
    m_errorHistory[toolName]++;
    m_recentErrors.append(error);
    
    if (m_recentErrors.size() > 10) {
        m_recentErrors.removeFirst();
    }
    
    qDebug() << "Tool execution error:" << toolName << error;
    
    // Circuit breaker: Stop execution if too many errors
    if (m_context.errorCount > 5) {
        qDebug() << "CIRCUIT BREAKER: Too many errors (" << m_context.errorCount << "), stopping execution";
        emit executionCompleted(false, QString("Execution stopped due to excessive errors. Last error: %1").arg(error));
        return;
    }
    
    // Check for specific repeated error patterns that indicate infinite loops
    if (toolName == "create_midi_clip" && error.contains("Track not found")) {
        qDebug() << "PREVENTING INFINITE LOOP: create_midi_clip failing repeatedly";
        emit executionCompleted(false, "Track creation/lookup system is broken. Cannot continue execution.");
        return;
    }
    
    // Attempt recovery if possible (but with limits)
    if (canRecoverFromError(error) && m_context.errorCount <= 3) {
        QJsonArray recoveryActions = suggestRecoveryActions(error);
        if (!recoveryActions.isEmpty()) {
            qDebug() << "Attempting error recovery with" << recoveryActions.size() << "actions";
            // Insert recovery actions into current sequence
            for (int i = recoveryActions.size() - 1; i >= 0; i--) {
                m_currentSequence.insert(m_currentStepIndex, recoveryActions[i]);
            }
            executeNextStep();
            return;
        }
    }
    
    emit errorRecoveryNeeded(error, suggestRecoveryActions(error));
    emit executionCompleted(false, QString("Failed at step %1 (%2): %3")
                                     .arg(m_currentStepIndex)
                                     .arg(toolName)
                                     .arg(error));
}

bool AiAgent::canRecoverFromError(const QString& error)
{
    QString lowerError = error.toLower();
    
    // Recoverable errors
    if (lowerError.contains("track not found") ||
        lowerError.contains("clip not found") ||
        lowerError.contains("invalid parameter") ||
        lowerError.contains("out of range")) {
        return true;
    }
    
    return false;
}

QJsonArray AiAgent::suggestRecoveryActions(const QString& error)
{
    QJsonArray actions;
    QString lowerError = error.toLower();
    
    if (lowerError.contains("track not found")) {
        actions.append(QJsonObject{
            {"tool", "create_track"},
            {"params", QJsonObject{
                {"type", "instrument"},
                {"name", "Recovery Track"}
            }}
        });
    }
    
    if (lowerError.contains("invalid parameter")) {
        // Could suggest parameter correction, but would need more context
        actions.append(QJsonObject{
            {"tool", "read_project"},
            {"params", QJsonObject{}}
        });
    }
    
    return actions;
}

// Parameter validation and sanitization
bool AiAgent::validateParameters(const QJsonObject& params, const QString& toolName)
{
    if (toolName == "set_tempo") {
        QJsonValue bpm = params["bpm"];
        if (!bpm.isDouble() || bpm.toDouble() < 60 || bpm.toDouble() > 200) {
            return false;
        }
    } else if (toolName == "write_notes") {
        QJsonValue notes = params["notes"];
        if (!notes.isArray()) return false;
        
        for (const QJsonValue& note : notes.toArray()) {
            QJsonObject noteObj = note.toObject();
            int key = noteObj["key"].toInt(-1);
            if (key < 0 || key > 127) return false;
            
            int velocity = noteObj["velocity"].toInt(100);
            if (velocity < 1 || velocity > 127) return false;
        }
    }
    
    return true;
}

QJsonObject AiAgent::sanitizeParameters(const QJsonObject& params, const QString& toolName)
{
    QJsonObject sanitized = params;
    
    if (toolName == "set_tempo") {
        double bpm = params["bpm"].toDouble(120);
        bpm = qBound(60.0, bpm, 200.0);
        sanitized["bpm"] = bpm;
    } else if (toolName == "write_notes") {
        QJsonArray notes = params["notes"].toArray();
        QJsonArray sanitizedNotes;
        
        for (const QJsonValue& note : notes) {
            QJsonObject noteObj = note.toObject();
            
            int key = qBound(0, noteObj["key"].toInt(60), 127);
            int velocity = qBound(1, noteObj["velocity"].toInt(100), 127);
            int startTicks = qMax(0, noteObj["start_ticks"].toInt(0));
            int lengthTicks = qMax(1, noteObj["length_ticks"].toInt(96));
            
            sanitizedNotes.append(QJsonObject{
                {"key", key},
                {"velocity", velocity},
                {"start_ticks", startTicks},
                {"length_ticks", lengthTicks}
            });
        }
        
        sanitized["notes"] = sanitizedNotes;
    }
    
    return sanitized;
}

void AiAgent::updateProjectState()
{
    Song* song = Engine::getSong();
    if (!song) return;
    
    m_context.projectState["tempo"] = song->getTempo();
    m_context.projectState["time_signature"] = QString("%1/%2")
        .arg(song->getTimeSigModel().getNumerator())
        .arg(song->getTimeSigModel().getDenominator());
    
    QStringList trackNames;
    for (Track* track : song->tracks()) {
        trackNames.append(track->name());
    }
    m_context.availableTracks = trackNames;
}

void AiAgent::initializeMusicalKnowledge()
{
    // Scale database
    m_scaleDatabase["major"] = QJsonArray{"C", "D", "E", "F", "G", "A", "B"};
    m_scaleDatabase["minor"] = QJsonArray{"C", "D", "Eb", "F", "G", "Ab", "Bb"};
    m_scaleDatabase["dorian"] = QJsonArray{"C", "D", "Eb", "F", "G", "A", "Bb"};
    m_scaleDatabase["pentatonic"] = QJsonArray{"C", "D", "E", "G", "A"};
    
    // Chord database
    QJsonObject majorChord;
    majorChord["intervals"] = QJsonArray{0, 4, 7};
    majorChord["quality"] = "major";
    m_chordDatabase["major"] = majorChord;
    
    QJsonObject minorChord;
    minorChord["intervals"] = QJsonArray{0, 3, 7};
    minorChord["quality"] = "minor";
    m_chordDatabase["minor"] = minorChord;
    
    // Genre templates with typical BPMs
    QJsonObject genreData;
    genreData["house"] = QJsonObject{{"bpm_range", QJsonArray{120, 130}}, {"typical_bpm", 126}};
    genreData["techno"] = QJsonObject{{"bpm_range", QJsonArray{125, 135}}, {"typical_bpm", 130}};
    genreData["trance"] = QJsonObject{{"bpm_range", QJsonArray{130, 140}}, {"typical_bpm", 135}};
    genreData["drum_and_bass"] = QJsonObject{{"bpm_range", QJsonArray{160, 180}}, {"typical_bpm", 174}};
    genreData["dubstep"] = QJsonObject{{"bpm_range", QJsonArray{135, 145}}, {"typical_bpm", 140}};
    genreData["trap"] = QJsonObject{{"bpm_range", QJsonArray{135, 160}}, {"typical_bpm", 140}};
    genreData["uk_garage"] = QJsonObject{{"bpm_range", QJsonArray{125, 135}}, {"typical_bpm", 130}};
    
    m_genreTemplates = genreData;
}

void AiAgent::initializeToolCapabilities()
{
    // Define capabilities for each tool
    m_toolCapabilities["set_tempo"] = {"set_tempo", {}, {"project_tempo"}, 1, 0.1, {}};
    m_toolCapabilities["create_track"] = {"create_track", {}, {"new_track"}, 2, 0.3, {}};
    m_toolCapabilities["create_midi_clip"] = {"create_midi_clip", {"track_exists"}, {"new_clip"}, 3, 0.2, {"create_track"}};
    m_toolCapabilities["write_notes"] = {"write_notes", {"clip_exists"}, {"notes_written"}, 4, 0.4, {"create_midi_clip"}};
    m_toolCapabilities["add_effect"] = {"add_effect", {"track_exists"}, {"effect_added"}, 3, 0.3, {"create_track"}};
    
    // Tool compatibility matrix
    QJsonObject ct; ct["create_midi_clip"] = true; ct["add_effect"] = true; m_toolCompatibility["create_track"] = ct;
    QJsonObject cmc; cmc["write_notes"] = true; m_toolCompatibility["create_midi_clip"] = cmc;
    
    m_criticalTools = QStringList() << "set_tempo" << "create_track" << "create_midi_clip";
}

QStringList AiAgent::getScaleNotes(const QString& key, const QString& scale)
{
    QStringList notes;
    QJsonArray scaleIntervals = m_scaleDatabase[scale].toArray();
    
    // Note mapping
    QHash<QString, int> noteToSemitone;
    noteToSemitone["c"] = 0;  noteToSemitone["db"] = 1;  noteToSemitone["d"] = 2;
    noteToSemitone["eb"] = 3; noteToSemitone["e"] = 4;   noteToSemitone["f"] = 5;
    noteToSemitone["gb"] = 6; noteToSemitone["g"] = 7;   noteToSemitone["ab"] = 8;
    noteToSemitone["a"] = 9;  noteToSemitone["bb"] = 10; noteToSemitone["b"] = 11;
    
    QStringList chromaticNotes = {"C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"};
    
    int rootSemitone = noteToSemitone[key.toLower()];
    
    for (const QJsonValue& interval : scaleIntervals) {
        int semitone = (rootSemitone + interval.toInt()) % 12;
        notes.append(chromaticNotes[semitone]);
    }
    
    return notes;
}

int AiAgent::getBPMForGenre(const QString& genre)
{
    QString normalizedGenre = genre.toLower().replace(" ", "_");
    QJsonObject genreInfo = m_genreTemplates[normalizedGenre].toObject();
    return genreInfo["typical_bpm"].toInt(120);
}

void AiAgent::resetSession()
{
    m_currentSessionId = QUuid::createUuid().toString();
    m_context.sessionId = m_currentSessionId;
    m_context.errorCount = 0;
    m_context.recentActions.clear();
    m_currentStepIndex = 0;
    m_recentErrors.clear();
}

void AiAgent::onExecutionTimer()
{
    // Tool execution timeout
    qDebug() << "Tool execution timeout at step" << m_currentStepIndex;
    handleExecutionError("Tool execution timeout", "timeout");
}

void AiAgent::onStateUpdateTimer()
{
    updateProjectState();
}

void AiAgent::updateMusicalContext(const AiToolResult& result)
{
    // Update context based on successful tool execution
    if (result.toolName == "set_tempo") {
        m_context.musicalContext["current_tempo"] = result.output.split(" ")[3].toInt(); // "Tempo set to X BPM"
    } else if (result.toolName == "create_track") {
        m_context.recentActions.append("created_track");
    } else if (result.toolName == "write_notes") {
        m_context.recentActions.append("wrote_notes");
    }
}

void AiAgent::trackToolUsage(const QString& toolName, bool success)
{
    // Track statistics for tool performance optimization
    Q_UNUSED(toolName)
    Q_UNUSED(success)
    // Could implement analytics here
}

QJsonObject AiAgent::getExecutionContext() const
{
    return QJsonObject{
        {"session_id", m_context.sessionId},
        {"project_state", m_context.projectState},
        {"musical_context", m_context.musicalContext},
        {"available_tracks", QJsonArray::fromStringList(m_context.availableTracks)},
        {"recent_actions", QJsonArray::fromStringList(m_context.recentActions)},
        {"error_count", m_context.errorCount}
    };
}

// MusicProductionTools implementation
QJsonArray MusicProductionTools::getComprehensiveToolDefinitions()
{
    QJsonArray tools;
    
    // Composition tools
    QJsonObject compositionTools = createCompositionTools();
    for (auto it = compositionTools.begin(); it != compositionTools.end(); ++it) {
        tools.append(it.value());
    }
    
    // Add arrangement, audio, mixing tools etc.
    // (Implementation would continue for all tool categories)
    
    return tools;
}

QJsonObject MusicProductionTools::createCompositionTools()
{
    QJsonObject tools;
    
    // Enhanced tool definitions with detailed schemas
    tools["set_project_key"] = QJsonObject{
        {"type", "custom"},
        {"name", "set_project_key"},
        {"description", "Set the musical key and scale for the project"},
        {"parameters", QJsonObject{
            {"key", QJsonObject{{"type", "string"}, {"enum", QJsonArray{"C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"}}}},
            {"scale", QJsonObject{{"type", "string"}, {"enum", QJsonArray{"major", "minor", "dorian", "mixolydian", "pentatonic"}}}}
        }}
    };
    
    tools["generate_chord_progression"] = QJsonObject{
        {"type", "custom"},
        {"name", "generate_chord_progression"},
        {"description", "Generate a chord progression in the specified key and style"},
        {"parameters", QJsonObject{
            {"key", QJsonObject{{"type", "string"}}},
            {"style", QJsonObject{{"type", "string"}, {"enum", QJsonArray{"pop", "house", "jazz", "classical", "funk"}}}},
            {"length_bars", QJsonObject{{"type", "integer"}, {"minimum", 1}, {"maximum", 32}}}
        }}
    };
    
    tools["create_bassline"] = QJsonObject{
        {"type", "custom"},
        {"name", "create_bassline"},
        {"description", "Create a bassline that follows the chord progression"},
        {"parameters", QJsonObject{
            {"track_name", QJsonObject{{"type", "string"}}},
            {"chord_track", QJsonObject{{"type", "string"}}},
            {"pattern_type", QJsonObject{{"type", "string"}, {"enum", QJsonArray{"root_notes", "walking", "syncopated", "arpeggiated"}}}}
        }}
    };
    
    return tools;
}

// =============================================================================
// INTELLIGENT MUSIC STYLE ANALYSIS SYSTEM
// =============================================================================

bool AiAgent::needsWebResearch(const QString& message)
{
    QString lowerMsg = message.toLower();
    
    // Check for specific artist names, obscure genres, or style references that need research
    QRegularExpression artistPattern("(style of|like|inspired by|similar to|sounds like)\\s+([a-zA-Z\\s]+)");
    QRegularExpressionMatch match = artistPattern.match(lowerMsg);
    
    if (match.hasMatch()) {
        QString reference = match.captured(2).trimmed();
        qDebug() << "Found style reference that may need research:" << reference;
        
        // Check if it's a common genre we already know about
        QStringList commonGenres = {"house", "techno", "trap", "hip hop", "drum and bass", "dubstep", 
                                   "trance", "ambient", "garage", "breakbeat", "jungle", "minimal", 
                                   "pop", "rock", "jazz", "classical", "funk", "disco"};
        
        return !commonGenres.contains(reference.toLower());
    }
    
    // Check for artist names or specific style references
    if (lowerMsg.contains(" style") || lowerMsg.contains(" sound") || lowerMsg.contains("inspired by")) {
        return true;
    }
    
    return false;
}

void AiAgent::performWebResearch(const QString& query)
{
    qDebug() << "Performing web research for musical style:" << query;
    
    // Extract the style/artist reference from the query
    QRegularExpression stylePattern("(style of|like|inspired by|similar to|sounds like)\\s+([a-zA-Z\\s]+)");
    QRegularExpressionMatch match = stylePattern.match(query.toLower());
    
    QString searchTerm;
    if (match.hasMatch()) {
        searchTerm = match.captured(2).trimmed() + " music style characteristics tempo";
    } else {
        searchTerm = query + " music style";
    }
    
    // Simulated web research (in a real implementation, use QNetworkAccessManager)
    // For now, we'll create a knowledge base lookup
    QJsonObject webData = simulateWebResearch(searchTerm);
    
    // Store research results in musical context
    if (!webData.isEmpty()) {
        m_context.musicalContext["web_research"] = webData;
        qDebug() << "Web research completed, found characteristics for:" << searchTerm;
    }
}

QJsonObject AiAgent::simulateWebResearch(const QString& searchTerm)
{
    // This simulates web research results. In production, this would use actual web search API
    QJsonObject result;
    QString term = searchTerm.toLower();
    
    // Enhanced knowledge base for various artists and styles
    if (term.contains("fred again")) {
        result["genre"] = "uk_garage";
        result["tempo"] = 128;
        result["characteristics"] = QJsonArray{
            "chopped_vocal_samples", "swung_drum_patterns", "organic_textures", 
            "emotional_builds", "sidechain_compression", "field_recordings"
        };
        result["instruments"] = QJsonArray{"drums", "bass", "vocal_chops", "pads", "percussion"};
        result["key_signature"] = "minor_keys_common";
        result["arrangement"] = "intro_buildup_drop_breakdown";
    }
    else if (term.contains("skrillex")) {
        result["genre"] = "dubstep";
        result["tempo"] = 140;
        result["characteristics"] = QJsonArray{
            "heavy_bass_drops", "glitchy_synths", "aggressive_leads", 
            "vocal_chops", "complex_rhythms", "mid_range_bass"
        };
        result["instruments"] = QJsonArray{"drums", "bass", "lead_synth", "vocal_chops", "fx"};
    }
    else if (term.contains("flume")) {
        result["genre"] = "future_bass";
        result["tempo"] = 150;
        result["characteristics"] = QJsonArray{
            "pitched_vocal_chops", "lush_pads", "trap_influenced_drums", 
            "melodic_leads", "wide_stereo_image", "organic_samples"
        };
        result["instruments"] = QJsonArray{"drums", "bass", "pads", "vocal_chops", "lead"};
    }
    else if (term.contains("four tet")) {
        result["genre"] = "electronic_ambient";
        result["tempo"] = 120;
        result["characteristics"] = QJsonArray{
            "field_recordings", "polyrhythmic_patterns", "textural_layers", 
            "organic_electronics", "subtle_melodies", "hypnotic_loops"
        };
        result["instruments"] = QJsonArray{"drums", "ambient_pads", "field_recordings", "synth_textures"};
    }
    else if (term.contains("deadmau5")) {
        result["genre"] = "progressive_house";
        result["tempo"] = 128;
        result["characteristics"] = QJsonArray{
            "long_builds", "filtered_sweeps", "driving_basslines", 
            "minimal_percussion", "atmospheric_pads", "melodic_leads"
        };
        result["instruments"] = QJsonArray{"drums", "bass", "lead_synth", "pads", "arpeggios"};
    }
    else if (term.contains("john summit")) {
        result["genre"] = "tech_house";
        result["tempo"] = 125;
        result["characteristics"] = QJsonArray{
            "groovy_basslines", "crisp_drums", "vocal_samples", 
            "rolling_percussion", "filtered_stabs", "energy_builds"
        };
        result["instruments"] = QJsonArray{"drums", "bass", "vocal_chops", "stabs", "percussion"};
        result["key_signature"] = "minor_keys_preferred";
        result["arrangement"] = "intro_groove_breakdown_drop";
    }
    // Add more artists as needed...
    
    return result;
}

QJsonObject AiAgent::analyzeWithGPT5(const QString& message)
{
    qDebug() << "=== AI-NATIVE MUSIC ORCHESTRATION ===";
    qDebug() << "User request:" << message;
    
    // Use AI-native system with retry logic - NO FALLBACKS
    QJsonObject aiResponse = makeAIAPICallWithRetry(message, 3);
    
    if (!aiResponse.isEmpty()) {
        // Process AI orchestration response
        QJsonObject processedResponse = processAIOrchestrationResponse(aiResponse);
        
        if (!processedResponse.isEmpty()) {
            qDebug() << "AI orchestration successful!";
            return processedResponse;
        }
    }
    
    qDebug() << "AI-native orchestration failed. No fallback system used as requested.";
    
    // Return empty object - user requested NO fallbacks
    QJsonObject failureResponse;
    failureResponse["error"] = "AI orchestration failed";
    failureResponse["message"] = "Unable to process request with AI system. Check API key configuration.";
    return failureResponse;
}

QJsonObject AiAgent::simulateGPT5Analysis(const QString& message)
{
    QJsonObject analysis;
    QString lowerMsg = message.toLower();
    
    // Intelligent pattern matching that considers context and style
    
    // Determine intent
    if (lowerMsg.contains("create") || lowerMsg.contains("make") || lowerMsg.contains("generate")) {
        if (lowerMsg.contains("beat") && !lowerMsg.contains("full") && !lowerMsg.contains("track")) {
            analysis["intent"] = "create_beat_pattern";
        } else {
            analysis["intent"] = "create_full_track";
        }
    } else if (lowerMsg.contains("modify") || lowerMsg.contains("change")) {
        analysis["intent"] = "modify_existing";
    }
    
    // Use web research data if available
    QJsonObject webData = m_context.musicalContext["web_research"].toObject();
    if (!webData.isEmpty()) {
        analysis["genre"] = webData["genre"].toString();
        analysis["tempo"] = webData["tempo"].toInt();
        analysis["elements"] = webData["instruments"].toArray();
        
        // Create style characteristics from web data
        QJsonObject styleChar;
        QJsonArray characteristics = webData["characteristics"].toArray();
        if (!characteristics.isEmpty()) {
            styleChar["primary_elements"] = characteristics;
            styleChar["rhythm_pattern"] = characteristics.first().toString();
            styleChar["sound_design"] = characteristics.size() > 1 ? characteristics[1].toString() : "modern";
        }
        analysis["style_characteristics"] = styleChar;
    } else {
        // Intelligent genre detection based on keywords and context
        analysis = analyzeGenreFromContext(lowerMsg);
    }
    
    // Determine complexity based on request scope
    if (lowerMsg.contains("simple") || lowerMsg.contains("basic")) {
        analysis["complexity"] = "low";
    } else if (lowerMsg.contains("complex") || lowerMsg.contains("full") || lowerMsg.contains("professional")) {
        analysis["complexity"] = "very_high";
    } else {
        analysis["complexity"] = "high";
    }
    
    // Generate instrument recommendations
    analysis["instruments"] = generateInstrumentRecommendations(analysis);
    
    return analysis;
}

QJsonObject AiAgent::analyzeGenreFromContext(const QString& lowerMsg)
{
    QJsonObject analysis;
    
    // Advanced genre detection using musical context clues
    if (lowerMsg.contains("house")) {
        analysis["genre"] = "house";
        analysis["tempo"] = 128;
        analysis["elements"] = QJsonArray{"drums", "bass", "pads", "leads"};
    }
    else if (lowerMsg.contains("trap")) {
        analysis["genre"] = "trap";
        analysis["tempo"] = 140;
        analysis["elements"] = QJsonArray{"drums", "808_bass", "leads", "vocal_chops"};
    }
    else if (lowerMsg.contains("ambient")) {
        analysis["genre"] = "ambient";
        analysis["tempo"] = 100;
        analysis["elements"] = QJsonArray{"pads", "textures", "subtle_drums", "field_recordings"};
    }
    else if (lowerMsg.contains("techno")) {
        analysis["genre"] = "techno";
        analysis["tempo"] = 130;
        analysis["elements"] = QJsonArray{"drums", "bass", "synth_sequences", "fx"};
    }
    else {
        // Default to electronic/house for general requests
        analysis["genre"] = "electronic";
        analysis["tempo"] = 120;
        analysis["elements"] = QJsonArray{"drums", "bass", "melody", "harmony"};
    }
    
    return analysis;
}

QJsonArray AiAgent::generateInstrumentRecommendations(const QJsonObject& analysis)
{
    QJsonArray instruments;
    QString genre = analysis["genre"].toString();
    
    // Generate specific instrument recommendations based on genre
    if (genre == "house" || genre == "uk_garage") {
        instruments.append(QJsonObject{{"type", "drums"}, {"preset", "kicker"}, {"role", "main_rhythm"}});
        instruments.append(QJsonObject{{"type", "bass"}, {"preset", "triple_oscillator"}, {"role", "bassline"}});
        instruments.append(QJsonObject{{"type", "pads"}, {"preset", "organic"}, {"role", "harmony"}});
        instruments.append(QJsonObject{{"type", "lead"}, {"preset", "watsyn"}, {"role", "melody"}});
    }
    else if (genre == "trap") {
        instruments.append(QJsonObject{{"type", "drums"}, {"preset", "kicker"}, {"role", "trap_pattern"}});
        instruments.append(QJsonObject{{"type", "bass"}, {"preset", "lb302"}, {"role", "808_bass"}});
        instruments.append(QJsonObject{{"type", "lead"}, {"preset", "monstro"}, {"role", "melodic_lead"}});
    }
    else if (genre == "ambient") {
        instruments.append(QJsonObject{{"type", "pads"}, {"preset", "organic"}, {"role", "atmospheric"}});
        instruments.append(QJsonObject{{"type", "textures"}, {"preset", "zynaddsubfx"}, {"role", "background"}});
        instruments.append(QJsonObject{{"type", "drums"}, {"preset", "audiofx"}, {"role", "subtle_rhythm"}});
    }
    else {
        // Default electronic setup
        instruments.append(QJsonObject{{"type", "drums"}, {"preset", "kicker"}, {"role", "main_rhythm"}});
        instruments.append(QJsonObject{{"type", "bass"}, {"preset", "triple_oscillator"}, {"role", "bassline"}});
        instruments.append(QJsonObject{{"type", "lead"}, {"preset", "bitinvader"}, {"role", "melody"}});
    }
    
    return instruments;
}

void AiAgent::fallbackAnalysis(const QString& message)
{
    qDebug() << "Using fallback analysis for:" << message;
    
    QString lowerMsg = message.toLower();
    QJsonObject fallback;
    
    // Basic intent detection
    if (lowerMsg.contains("beat") || lowerMsg.contains("drum")) {
        fallback["intent"] = "create_beat_pattern";
        fallback["elements"] = QJsonArray{"drums"};
    } else {
        fallback["intent"] = "create_full_track";
        fallback["elements"] = QJsonArray{"drums", "bass", "melody"};
    }
    
    fallback["genre"] = "electronic";
    fallback["tempo"] = 120;
    fallback["complexity"] = "medium";
    
    m_context.musicalContext = fallback;
}

// =============================================================================
// DYNAMIC TOOL SEQUENCE GENERATION
// =============================================================================

QJsonArray AiAgent::generateDynamicToolSequence(const QJsonObject& styleAnalysis)
{
    qDebug() << "Generating dynamic tool sequence from style analysis";
    
    QJsonArray sequence;
    QString genre = styleAnalysis["genre"].toString();
    QString intent = styleAnalysis["intent"].toString();
    int tempo = styleAnalysis["tempo"].toInt(120);
    QJsonArray elements = styleAnalysis["elements"].toArray();
    QJsonArray instruments = styleAnalysis["instruments"].toArray();
    
    // 1. Set project parameters based on analysis
    sequence.append(QJsonObject{
        {"tool", "set_tempo"},
        {"params", QJsonObject{{"bpm", tempo}}}
    });
    
    qDebug() << "Creating tracks for genre:" << genre << "with elements:" << elements;
    
    // 2. Create tracks dynamically based on analyzed instruments
    for (auto instrumentValue : instruments) {
        QJsonObject instrument = instrumentValue.toObject();
        QString type = instrument["type"].toString();
        QString preset = instrument["preset"].toString();
        QString role = instrument["role"].toString();
        
        // Create track with intelligent naming and preset selection
        QString trackName = capitalizeFirst(type);
        sequence.append(QJsonObject{
            {"tool", "create_track"},
            {"params", QJsonObject{
                {"type", "instrument"},
                {"name", trackName},
                {"instrument", preset}
            }}
        });
        
        // 3. Create MIDI clip for each instrument
        int lengthBars = (intent == "create_beat_pattern") ? 1 : 4;
        sequence.append(QJsonObject{
            {"tool", "create_midi_clip"},
            {"params", QJsonObject{
                {"track_name", trackName},
                {"start_ticks", 0},
                {"length_ticks", TimePos::ticksPerBar() * lengthBars}
            }}
        });
        
        // 4. Generate AI-driven musical content
        QJsonArray notes = generateAIMusicalContent(type, styleAnalysis);
        if (!notes.isEmpty()) {
            sequence.append(QJsonObject{
                {"tool", "write_notes"},
                {"params", QJsonObject{
                    {"track_name", trackName},
                    {"clip_index", 0},
                    {"notes", notes}
                }}
            });
        }
        
        // 5. Add genre-appropriate effects
        QJsonArray effects = getEffectsForGenreAndInstrument(genre, type);
        for (auto effectValue : effects) {
            sequence.append(QJsonObject{
                {"tool", "add_effect"},
                {"params", QJsonObject{
                    {"track_name", trackName},
                    {"effect_name", effectValue.toString()}
                }}
            });
        }
    }
    
    // 6. Add final validation
    sequence.append(QJsonObject{
        {"tool", "read_project"},
        {"params", QJsonObject{}}
    });
    
    qDebug() << "Generated dynamic sequence with" << sequence.size() << "steps";
    return sequence;
}

QJsonArray AiAgent::createBasicSequence(const QString& goal)
{
    QJsonArray sequence;
    
    // Basic fallback sequence
    sequence.append(QJsonObject{
        {"tool", "set_tempo"},
        {"params", QJsonObject{{"bpm", 120}}}
    });
    
    sequence.append(QJsonObject{
        {"tool", "create_track"},
        {"params", QJsonObject{
            {"type", "instrument"},
            {"name", "Drums"},
            {"instrument", "kicker"}
        }}
    });
    
    sequence.append(QJsonObject{
        {"tool", "create_midi_clip"},
        {"params", QJsonObject{
            {"track_name", "Drums"},
            {"start_ticks", 0},
            {"length_ticks", TimePos::ticksPerBar()}
        }}
    });
    
    // Basic 4/4 drum pattern
    QJsonArray basicDrums;
    basicDrums.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
    basicDrums.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
    
    sequence.append(QJsonObject{
        {"tool", "write_notes"},
        {"params", QJsonObject{
            {"track_name", "Drums"},
            {"clip_index", 0},
            {"notes", basicDrums}
        }}
    });
    
    return sequence;
}

QJsonArray AiAgent::generateMusicalContent(const QString& instrumentType, const QString& genre, const QString& role, int tempo)
{
    QJsonArray notes;
    
    if (instrumentType == "drums") {
        notes = generateDrumPattern(genre, tempo);
    } else if (instrumentType == "bass") {
        notes = generateBassPattern(genre, tempo);
    } else if (instrumentType == "pads" || instrumentType == "chords") {
        notes = generateChordPattern(genre);
    } else if (instrumentType == "lead" || instrumentType == "melody") {
        notes = generateMelodyPattern(genre, tempo);
    }
    
    qDebug() << "Generated" << notes.size() << "notes for" << instrumentType << "in" << genre;
    return notes;
}

QJsonArray AiAgent::generateDrumPattern(const QString& genre, int tempo)
{
    QJsonArray pattern;
    
    if (genre == "uk_garage" || genre == "house") {
        // UK Garage/House pattern with swing
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 105}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 95}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 1152}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
        
        // Add swung hi-hats
        for (int i = 0; i < 16; i++) {
            int tick = i * 96;
            if (i % 2 == 1) tick += 16; // Add swing
            int velocity = 75 + (i % 3) * 5; // Vary velocity
            pattern.append(QJsonObject{{"start_ticks", tick}, {"key", 42}, {"velocity", velocity}, {"length_ticks", 48}});
        }
    }
    else if (genre == "trap") {
        // Trap pattern with 808 focus
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 127}, {"length_ticks", 200}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 115}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 120}, {"length_ticks", 200}});
        pattern.append(QJsonObject{{"start_ticks", 1344}, {"key", 38}, {"velocity", 110}, {"length_ticks", 96}});
        
        // Add trap hi-hats (fast)
        for (int i = 0; i < 32; i++) {
            int tick = i * 48;
            int velocity = 60 + (i % 4) * 10;
            pattern.append(QJsonObject{{"start_ticks", tick}, {"key", 42}, {"velocity", velocity}, {"length_ticks", 24}});
        }
    }
    else if (genre == "tech_house") {
        // Tech house pattern - groovy and rolling
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 110}, {"length_ticks", 120}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 105}, {"length_ticks", 120}});
        pattern.append(QJsonObject{{"start_ticks", 1152}, {"key", 38}, {"velocity", 95}, {"length_ticks", 96}});
        
        // Rolling percussion (shakers, percs)
        for (int i = 0; i < 8; i++) {
            int tick = i * 192;
            pattern.append(QJsonObject{{"start_ticks", tick + 96}, {"key", 44}, {"velocity", 70 + (i % 2) * 10}, {"length_ticks", 48}});
        }
        
        // Off-beat hi-hats
        for (int i = 1; i < 16; i += 2) {
            int tick = i * 96;
            pattern.append(QJsonObject{{"start_ticks", tick}, {"key", 42}, {"velocity", 65}, {"length_ticks", 48}});
        }
    }
    else if (genre == "ambient") {
        // Minimal ambient percussion
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 60}, {"length_ticks", 200}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 38}, {"velocity", 55}, {"length_ticks", 150}});
        pattern.append(QJsonObject{{"start_ticks", 1536}, {"key", 42}, {"velocity", 50}, {"length_ticks", 100}});
    }
    else {
        // Default electronic pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 1152}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
    }
    
    return pattern;
}

QJsonArray AiAgent::generateBassPattern(const QString& genre, int tempo)
{
    QJsonArray pattern;
    
    // Generate bass patterns based on genre characteristics
    if (genre == "house" || genre == "uk_garage") {
        // House-style bassline (F minor scale)
        int bassTicks[] = {0, 768, 1536, 2304};
        int bassNotes[] = {41, 39, 36, 41}; // F-Eb-C-F
        for (int i = 0; i < 4; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", bassTicks[i]},
                {"key", bassNotes[i]},
                {"velocity", 90},
                {"length_ticks", 600}
            });
        }
    }
    else if (genre == "trap") {
        // 808-style bass pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 41}, {"velocity", 127}, {"length_ticks", 800}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 44}, {"velocity", 120}, {"length_ticks", 400}});
        pattern.append(QJsonObject{{"start_ticks", 1536}, {"key", 39}, {"velocity", 125}, {"length_ticks", 600}});
    }
    else {
        // Default bass pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 41}, {"velocity", 90}, {"length_ticks", 768}});
        pattern.append(QJsonObject{{"start_ticks", 1536}, {"key", 44}, {"velocity", 85}, {"length_ticks", 768}});
    }
    
    return pattern;
}

QJsonArray AiAgent::generateChordPattern(const QString& genre)
{
    QJsonArray pattern;
    
    // Generate chord progressions based on genre
    int chordPositions[] = {0, 768, 1536, 2304};
    
    if (genre == "house" || genre == "uk_garage") {
        // Minor chord progression (vi-IV-I-V in C major = Am-F-C-G)
        int chordRoots[] = {57, 53, 48, 55}; // A-F-C-G
        int minorChord[] = {0, 3, 7}; // Minor triad
        
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 3; j++) {
                pattern.append(QJsonObject{
                    {"start_ticks", chordPositions[i]},
                    {"key", chordRoots[i] + minorChord[j]},
                    {"velocity", 75},
                    {"length_ticks", 700}
                });
            }
        }
    } else {
        // Default major chord progression
        int chordRoots[] = {48, 53, 57, 55}; // C-F-A-G
        int majorChord[] = {0, 4, 7}; // Major triad
        
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 3; j++) {
                pattern.append(QJsonObject{
                    {"start_ticks", chordPositions[i]},
                    {"key", chordRoots[i] + majorChord[j]},
                    {"velocity", 70},
                    {"length_ticks", 700}
                });
            }
        }
    }
    
    return pattern;
}

QJsonArray AiAgent::generateMelodyPattern(const QString& genre, int tempo)
{
    QJsonArray pattern;
    
    // Generate melodies based on genre characteristics
    if (genre == "ambient") {
        // Slow, atmospheric melody
        int melodyNotes[] = {72, 74, 76, 74, 72, 69, 67, 69};
        for (int i = 0; i < 8; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", i * 384},
                {"key", melodyNotes[i]},
                {"velocity", 60 + i * 2},
                {"length_ticks", 300}
            });
        }
    } else {
        // More rhythmic melody for electronic genres
        int melodyNotes[] = {72, 76, 79, 74, 72, 74, 76, 72};
        for (int i = 0; i < 8; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", i * 192},
                {"key", melodyNotes[i]},
                {"velocity", 80 + (i % 3) * 10},
                {"length_ticks", 150}
            });
        }
    }
    
    return pattern;
}

QJsonArray AiAgent::getEffectsForGenreAndInstrument(const QString& genre, const QString& instrument)
{
    QJsonArray effects;
    
    if (instrument == "bass") {
        effects.append("bassbooster");
        if (genre == "trap") {
            effects.append("compressor");
        }
    } else if (instrument == "drums") {
        effects.append("compressor");
        if (genre == "house" || genre == "uk_garage") {
            effects.append("delay");
        }
    } else if (instrument == "lead") {
        effects.append("delay");
        effects.append("eq");
    }
    
    return effects;
}

QString AiAgent::capitalizeFirst(const QString& str)
{
    if (str.isEmpty()) return str;
    return str[0].toUpper() + str.mid(1);
}

// =============================================================================
// 100% AI-NATIVE MUSIC ANALYSIS SYSTEM
// =============================================================================

QJsonObject AiAgent::makeAIAPICall(const QString& message)
{
    qDebug() << "Making AI API call for musical orchestration";
    
    // Get OpenAI API key - REQUIRED for AI-native operation
    QString apiKey = getOpenAIAPIKey();
    
    if (apiKey.isEmpty()) {
        qDebug() << "ERROR: No OpenAI API key found. AI-native system requires API key.";
        qDebug() << "Please set OPENAI_API_KEY environment variable or create .envs file";
        // Return empty - we'll retry, no fallbacks
        return QJsonObject();
    }
    
    // Create comprehensive AI orchestration prompt with full LMMS knowledge
    QString availableTools = getLMMSToolsDescription();
    QString availableInstruments = getLMMSInstrumentsDescription();
    
    QString prompt = QString(
        "You are an AI music producer with complete access to LMMS (Linux Multimedia Studio). "
        "Your task is to orchestrate the creation of music using the available tools.\\n\\n"
        "USER REQUEST: \\\"%1\\\"\\n\\n"
        "AVAILABLE LMMS TOOLS:\\n%2\\n\\n"
        "AVAILABLE LMMS INSTRUMENTS:\\n%3\\n\\n"
        "TASK: Create a detailed step-by-step orchestration plan in JSON format:\\n"
        "{"
        "  \\\"analysis\\\": {"
        "    \\\"musical_style\\\": \\\"description of the musical style requested\\\","
        "    \\\"tempo\\\": BPM_number,"
        "    \\\"key\\\": \\\"musical key\\\","
        "    \\\"mood\\\": \\\"emotional description\\\","
        "    \\\"complexity\\\": \\\"assessment of complexity needed\\\""
        "  },"
        "  \\\"orchestration_plan\\\": ["
        "    {"
        "      \\\"step\\\": 1,"
        "      \\\"tool\\\": \\\"exact_tool_name\\\","
        "      \\\"params\\\": {\\\"param_name\\\": \\\"value\\\"},"
        "      \\\"reasoning\\\": \\\"why this tool and these parameters\\\""
        "    }"
        "  ],"
        "  \\\"expected_outcome\\\": \\\"description of what will be created\\\""
        "}"
        "\\n\\nBe thorough - create a complete track with multiple instruments, patterns, and effects. "
        "Use your musical knowledge to select appropriate tools and parameters."
    ).arg(message, availableTools, availableInstruments);
    
    // Make HTTP request to OpenAI API
    QNetworkAccessManager* manager = new QNetworkAccessManager(this);
    QNetworkRequest request(QUrl("https://api.openai.com/v1/responses"));
    
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setRawHeader("Authorization", ("Bearer " + apiKey).toUtf8());
    
    QJsonObject requestBody;
    requestBody["model"] = "gpt-5";
    QJsonObject reasoning; reasoning["effort"] = "medium"; requestBody["reasoning"] = reasoning;
    QJsonObject text; text["verbosity"] = "medium"; requestBody["text"] = text;
    QJsonArray input;
    QJsonObject sys; sys["role"] = "system"; sys["content"] =
        "You are an expert music producer and AI assistant specialized in analyzing musical requests and providing detailed technical specifications.";
    QJsonObject usr; usr["role"] = "user"; usr["content"] = prompt;
    input.append(sys);
    input.append(usr);
    requestBody["input"] = input;
    
    QJsonDocument requestDoc(requestBody);
    QByteArray requestData = requestDoc.toJson();
    
    // Send request synchronously (for simplicity)
    QEventLoop loop;
    QNetworkReply* reply = manager->post(request, requestData);
    connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();
    
    QJsonObject result;
    if (reply->error() == QNetworkReply::NoError) {
        QByteArray responseData = reply->readAll();
        QJsonDocument responseDoc = QJsonDocument::fromJson(responseData);
        QJsonObject response = responseDoc.object();
        
        if (response.contains("choices")) {
            QJsonArray choices = response["choices"].toArray();
            if (!choices.isEmpty()) {
                QJsonObject choice = choices[0].toObject();
                QJsonObject responseMessage = choice["message"].toObject();
                QString content = responseMessage["content"].toString();
                
                // Try to parse JSON from the response
                QJsonParseError error;
                QJsonDocument contentDoc = QJsonDocument::fromJson(content.toUtf8(), &error);
                if (error.error == QJsonParseError::NoError) {
                    result = contentDoc.object();
                    qDebug() << "Successfully received AI analysis from API";
                } else {
                    qDebug() << "Failed to parse AI response as JSON:" << error.errorString();
                }
            }
        }
    } else {
        qDebug() << "API request failed:" << reply->errorString();
    }
    
    reply->deleteLater();
    return result;
}

QJsonObject AiAgent::performAdvancedAIReasoning(const QString& message)
{
    qDebug() << "Performing advanced AI reasoning for:" << message;
    
    // Use semantic analysis to understand the musical request
    QJsonObject semantics = analyzeMusicalSemantics(message);
    
    // Generate musical characteristics using AI reasoning
    QJsonObject analysis;
    
    // Analyze intent using natural language processing concepts
    QString lowerMsg = message.toLower();
    if (lowerMsg.contains("create") || lowerMsg.contains("make") || lowerMsg.contains("generate")) {
        if (lowerMsg.contains("beat") && !lowerMsg.contains("track")) {
            analysis["intent"] = "create_beat";
        } else {
            analysis["intent"] = "create_full_track";
        }
    } else if (lowerMsg.contains("modify") || lowerMsg.contains("change") || lowerMsg.contains("add")) {
        analysis["intent"] = "modify_existing";
    } else {
        analysis["intent"] = "create_full_track";
    }
    
    // Use semantic analysis results
    analysis["genre"] = semantics["inferred_genre"].toString();
    analysis["tempo"] = semantics["tempo"].toInt();
    analysis["mood"] = semantics["mood"].toString();
    analysis["complexity"] = semantics["complexity"].toString();
    
    // Generate instrument recommendations using AI logic
    QJsonArray instruments = generateAIInstrumentSelection(semantics);
    analysis["instruments"] = instruments;
    
    // Also populate elements for compatibility
    QJsonArray elements;
    for (auto instValue : instruments) {
        QJsonObject inst = instValue.toObject();
        elements.append(inst["type"].toString());
    }
    analysis["elements"] = elements;
    
    qDebug() << "Generated" << instruments.size() << "instruments:" << instruments;
    
    // Add musical characteristics
    QJsonObject characteristics;
    characteristics["rhythm_pattern"] = semantics["rhythm_style"].toString();
    characteristics["harmonic_structure"] = semantics["harmony_type"].toString();
    characteristics["sound_design"] = semantics["sound_characteristics"].toString();
    characteristics["arrangement_style"] = semantics["arrangement"].toString();
    analysis["style_characteristics"] = characteristics;
    
    // Set musical parameters
    analysis["key_signature"] = semantics["key"].toString();
    analysis["time_signature"] = "4/4"; // Default, could be inferred
    
    qDebug() << "Advanced AI reasoning complete:" << QJsonDocument(analysis).toJson(QJsonDocument::Compact);
    return analysis;
}

QJsonObject AiAgent::analyzeMusicalSemantics(const QString& message)
{
    qDebug() << "Analyzing musical semantics";
    
    QJsonObject semantics;
    QString text = message.toLower();
    
    // Semantic analysis for mood and energy
    QStringList energeticWords = {"energetic", "upbeat", "driving", "powerful", "intense", "hard", "aggressive", "pumping"};
    QStringList chillWords = {"chill", "relaxed", "ambient", "soft", "gentle", "smooth", "mellow", "calm"};
    QStringList darkWords = {"dark", "industrial", "heavy", "deep", "underground", "gritty", "distorted"};
    QStringList upliftingWords = {"uplifting", "happy", "bright", "euphoric", "positive", "festival", "anthem"};
    
    QString mood = "neutral";
    if (containsAny(text, energeticWords)) mood = "energetic";
    else if (containsAny(text, chillWords)) mood = "chill";
    else if (containsAny(text, darkWords)) mood = "dark";
    else if (containsAny(text, upliftingWords)) mood = "uplifting";
    
    semantics["mood"] = mood;
    
    // Infer tempo from context and mood
    int baseTempo = 120;
    if (mood == "energetic") baseTempo = 140;
    else if (mood == "chill") baseTempo = 100;
    else if (text.contains("fast")) baseTempo = 150;
    else if (text.contains("slow")) baseTempo = 90;
    
    // Extract explicit BPM if mentioned
    QRegularExpression bpmRegex("(\\d+)\\s*(bpm|beats)");
    QRegularExpressionMatch bpmMatch = bpmRegex.match(text);
    if (bpmMatch.hasMatch()) {
        baseTempo = bpmMatch.captured(1).toInt();
    }
    
    semantics["tempo"] = baseTempo;
    
    // Infer genre from musical terminology and context
    QString genre = inferGenreFromSemantics(text, mood);
    semantics["inferred_genre"] = genre;
    
    // Determine complexity from request scope
    QString complexity = "medium";
    if (text.contains("simple") || text.contains("basic") || text.contains("minimal")) {
        complexity = "low";
    } else if (text.contains("complex") || text.contains("detailed") || text.contains("professional") || text.contains("full")) {
        complexity = "high";
    } else if (text.contains("advanced") || text.contains("intricate")) {
        complexity = "very_high";
    }
    
    semantics["complexity"] = complexity;
    
    // Infer musical characteristics
    semantics["rhythm_style"] = inferRhythmStyle(genre, mood);
    semantics["harmony_type"] = inferHarmonyType(genre, mood);
    semantics["sound_characteristics"] = inferSoundDesign(genre, mood);
    semantics["arrangement"] = inferArrangement(genre, complexity);
    semantics["key"] = inferKeySignature(mood);
    
    return semantics;
}

QString AiAgent::inferGenreFromSemantics(const QString& text, const QString& mood)
{
    // Advanced semantic genre inference with better pattern recognition
    qDebug() << "Inferring genre from text:" << text << "mood:" << mood;
    
    // Specific multi-word genre detection first
    if (text.contains("drum and bass") || text.contains("dnb")) {
        return "drum_and_bass";
    } else if (text.contains("future bass")) {
        return "future_bass";
    } else if (text.contains("uk garage")) {
        return "uk_garage";
    }
    
    // Single word genre detection
    QStringList houseGenres = {"house", "deep", "tech", "progressive"};
    QStringList trapGenres = {"trap", "hip hop", "rap", "808"};
    QStringList ambientGenres = {"ambient", "atmospheric", "drone", "cinematic"};
    QStringList technoGenres = {"techno", "industrial", "mechanical"};
    QStringList electronicGenres = {"electronic", "edm", "synth", "digital"};
    
    if (containsAny(text, houseGenres)) {
        if (text.contains("tech")) return "tech_house";
        if (text.contains("deep")) return "deep_house";
        if (text.contains("progressive")) return "progressive_house";
        return "house";
    } else if (containsAny(text, trapGenres)) {
        return "trap";
    } else if (containsAny(text, ambientGenres)) {
        return "ambient";
    } else if (containsAny(text, technoGenres)) {
        return "techno";
    } else if (containsAny(text, electronicGenres)) {
        // Infer electronic subgenre from mood
        if (mood == "energetic") return "electronic_dance";
        if (mood == "dark") return "dark_electronic";
        if (mood == "chill") return "chill_electronic";
        return "electronic";
    }
    
    // Default inference based on mood and context
    if (text.contains("fast") && text.contains("beat")) {
        if (mood == "energetic") return "electronic_dance";
        return "electronic";
    }
    
    if (mood == "energetic") return "electronic_dance";
    if (mood == "chill") return "ambient";
    if (mood == "dark") return "dark_electronic";
    
    return "electronic";
}

QString AiAgent::inferRhythmStyle(const QString& genre, const QString& mood)
{
    if (genre.contains("house")) return "four_on_floor_with_swing";
    if (genre.contains("drum_and_bass")) return "breakbeat_fast_chopped";
    if (genre.contains("trap")) return "syncopated_with_rolls";
    if (genre.contains("ambient")) return "minimal_atmospheric";
    if (genre.contains("techno")) return "driving_mechanical";
    if (mood == "energetic") return "driving_rhythmic";
    return "steady_electronic";
}

QString AiAgent::inferHarmonyType(const QString& genre, const QString& mood)
{
    if (mood == "dark") return "minor_progressions";
    if (mood == "uplifting") return "major_uplifting";
    if (genre.contains("ambient")) return "atmospheric_pads";
    if (genre.contains("house")) return "classic_house_chords";
    return "modern_electronic";
}

QString AiAgent::inferSoundDesign(const QString& genre, const QString& mood)
{
    if (genre.contains("house")) return "warm_analog_synths";
    if (genre.contains("trap")) return "digital_harsh_leads";
    if (genre.contains("ambient")) return "evolving_textures";
    if (mood == "dark") return "distorted_bass_heavy";
    if (mood == "energetic") return "bright_aggressive_synths";
    return "modern_electronic_sounds";
}

QString AiAgent::inferArrangement(const QString& genre, const QString& complexity)
{
    if (complexity == "low") return "loop_based";
    if (complexity == "very_high") return "complex_multi_section";
    if (genre.contains("house")) return "intro_buildup_drop_breakdown";
    if (genre.contains("ambient")) return "evolving_atmospheric";
    return "standard_electronic_structure";
}

QString AiAgent::inferKeySignature(const QString& mood)
{
    if (mood == "dark") return "Am"; // A minor
    if (mood == "uplifting") return "C"; // C major
    if (mood == "energetic") return "G"; // G major
    return "C"; // Default
}

QJsonArray AiAgent::generateAIInstrumentSelection(const QJsonObject& semantics)
{
    QJsonArray instruments;
    QString genre = semantics["inferred_genre"].toString();
    QString mood = semantics["mood"].toString();
    QString complexity = semantics["complexity"].toString();
    
    // AI-driven instrument selection based on analysis
    
    // Always include drums for rhythmic music
    if (genre != "ambient") {
        QString drumPreset = selectDrumPreset(genre, mood);
        instruments.append(QJsonObject{
            {"type", "drums"},
            {"preset", drumPreset},
            {"role", "main_rhythm"}
        });
    }
    
    // Bass selection
    QString bassPreset = selectBassPreset(genre, mood);
    instruments.append(QJsonObject{
        {"type", "bass"},
        {"preset", bassPreset},
        {"role", "bassline"}
    });
    
    // Melodic elements
    if (complexity != "low") {
        QString leadPreset = selectLeadPreset(genre, mood);
        instruments.append(QJsonObject{
            {"type", "lead"},
            {"preset", leadPreset},
            {"role", "melody"}
        });
        
        // Add pads for atmospheric content
        if (genre.contains("house") || genre.contains("ambient") || mood == "uplifting") {
            instruments.append(QJsonObject{
                {"type", "pads"},
                {"preset", "organic"},
                {"role", "atmosphere"}
            });
        }
    }
    
    return instruments;
}

QString AiAgent::selectDrumPreset(const QString& genre, const QString& mood)
{
    if (genre.contains("house") || genre.contains("tech")) return "kicker";
    if (genre.contains("trap")) return "kicker"; // Could use different preset
    if (mood == "energetic") return "kicker";
    return "kicker"; // Default
}

QString AiAgent::selectBassPreset(const QString& genre, const QString& mood)
{
    if (genre.contains("house")) return "triple_oscillator";
    if (genre.contains("trap")) return "lb302"; // 808-style
    if (genre.contains("ambient")) return "organic";
    if (mood == "dark") return "monstro";
    return "triple_oscillator";
}

QString AiAgent::selectLeadPreset(const QString& genre, const QString& mood)
{
    if (genre.contains("house")) return "watsyn";
    if (genre.contains("trap")) return "bitinvader";
    if (genre.contains("ambient")) return "zynaddsubfx";
    if (mood == "energetic") return "monstro";
    return "watsyn";
}

bool AiAgent::containsAny(const QString& text, const QStringList& words)
{
    for (const QString& word : words) {
        if (text.contains(word)) return true;
    }
    return false;
}

QJsonArray AiAgent::generateAIMusicalContent(const QString& instrumentType, const QJsonObject& aiAnalysis)
{
    qDebug() << "Generating AI-driven musical content for" << instrumentType;
    qDebug() << "Using AI analysis:" << QJsonDocument(aiAnalysis).toJson(QJsonDocument::Compact);
    
    QString genre = aiAnalysis["genre"].toString();
    QString mood = aiAnalysis["mood"].toString();
    int tempo = aiAnalysis["tempo"].toInt(120);
    QString complexity = aiAnalysis["complexity"].toString();
    QJsonObject styleChar = aiAnalysis["style_characteristics"].toObject();
    
    QJsonArray notes;
    
    if (instrumentType == "drums") {
        notes = generateAIDrumPattern(genre, mood, tempo, styleChar);
    } else if (instrumentType == "bass") {
        notes = generateAIBassPattern(genre, mood, tempo, styleChar);
    } else if (instrumentType == "pads" || instrumentType == "chords") {
        notes = generateAIChordPattern(genre, mood, aiAnalysis["key_signature"].toString(), styleChar);
    } else if (instrumentType == "lead" || instrumentType == "melody") {
        notes = generateAIMelodyPattern(genre, mood, tempo, aiAnalysis["key_signature"].toString(), styleChar);
    }
    
    qDebug() << "Generated" << notes.size() << "AI-driven notes for" << instrumentType;
    return notes;
}

QJsonArray AiAgent::generateAIDrumPattern(const QString& genre, const QString& mood, int tempo, const QJsonObject& styleChar)
{
    QJsonArray pattern;
    QString rhythmStyle = styleChar["rhythm_pattern"].toString();
    
    qDebug() << "Generating AI drum pattern - Genre:" << genre << "Mood:" << mood << "Rhythm:" << rhythmStyle;
    
    // AI-driven drum pattern generation based on analysis
    if (rhythmStyle.contains("four_on_floor") || genre.contains("house")) {
        // House-style four-on-floor with groove
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 110}, {"length_ticks", 120}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 105}, {"length_ticks", 120}});
        pattern.append(QJsonObject{{"start_ticks", 1152}, {"key", 38}, {"velocity", 95}, {"length_ticks", 96}});
        
        // Add groove elements based on mood
        if (mood == "energetic") {
            // More aggressive hi-hats
            for (int i = 0; i < 16; i++) {
                int tick = i * 96;
                int velocity = 70 + (i % 3) * 10;
                pattern.append(QJsonObject{{"start_ticks", tick}, {"key", 42}, {"velocity", velocity}, {"length_ticks", 48}});
            }
        } else {
            // Subtle off-beat hats
            for (int i = 1; i < 16; i += 2) {
                int tick = i * 96;
                pattern.append(QJsonObject{{"start_ticks", tick}, {"key", 42}, {"velocity", 65}, {"length_ticks", 48}});
            }
        }
    } else if (rhythmStyle.contains("syncopated") || genre.contains("trap")) {
        // Trap-style syncopated pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 127}, {"length_ticks", 200}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 115}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 120}, {"length_ticks", 200}});
        
        // Fast hi-hat rolls
        for (int i = 0; i < 32; i++) {
            int tick = i * 48;
            int velocity = 60 + (i % 4) * 8;
            pattern.append(QJsonObject{{"start_ticks", tick}, {"key", 42}, {"velocity", velocity}, {"length_ticks", 24}});
        }
    } else if (rhythmStyle.contains("minimal") || genre.contains("ambient")) {
        // Minimal atmospheric percussion
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 60}, {"length_ticks", 200}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 38}, {"velocity", 55}, {"length_ticks", 150}});
        pattern.append(QJsonObject{{"start_ticks", 1536}, {"key", 42}, {"velocity", 50}, {"length_ticks", 100}});
    } else {
        // Default AI-generated pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
        pattern.append(QJsonObject{{"start_ticks", 1152}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
    }
    
    return pattern;
}

QJsonArray AiAgent::generateAIBassPattern(const QString& genre, const QString& mood, int tempo, const QJsonObject& styleChar)
{
    QJsonArray pattern;
    QString harmonyType = styleChar["harmonic_structure"].toString();
    
    qDebug() << "Generating AI bass pattern - Genre:" << genre << "Mood:" << mood << "Harmony:" << harmonyType;
    
    if (genre.contains("house") || harmonyType.contains("classic_house")) {
        // House-style bassline with groove
        int bassTicks[] = {0, 768, 1536, 2304};
        int bassNotes[] = {41, 39, 36, 41}; // F-Eb-C-F
        for (int i = 0; i < 4; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", bassTicks[i]},
                {"key", bassNotes[i]},
                {"velocity", mood == "energetic" ? 95 : 85},
                {"length_ticks", 600}
            });
        }
    } else if (genre.contains("trap") || harmonyType.contains("digital_harsh")) {
        // 808-style bass pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 41}, {"velocity", 127}, {"length_ticks", 800}});
        pattern.append(QJsonObject{{"start_ticks", 768}, {"key", 44}, {"velocity", 120}, {"length_ticks", 400}});
        pattern.append(QJsonObject{{"start_ticks", 1536}, {"key", 39}, {"velocity", 125}, {"length_ticks", 600}});
    } else {
        // AI-generated bass pattern
        pattern.append(QJsonObject{{"start_ticks", 0}, {"key", 41}, {"velocity", 90}, {"length_ticks", 768}});
        pattern.append(QJsonObject{{"start_ticks", 1536}, {"key", 44}, {"velocity", 85}, {"length_ticks", 768}});
    }
    
    return pattern;
}

QJsonArray AiAgent::generateAIChordPattern(const QString& genre, const QString& mood, const QString& key, const QJsonObject& styleChar)
{
    QJsonArray pattern;
    QString harmonyType = styleChar["harmonic_structure"].toString();
    
    qDebug() << "Generating AI chord pattern - Genre:" << genre << "Mood:" << mood << "Key:" << key << "Harmony:" << harmonyType;
    
    int chordPositions[] = {0, 768, 1536, 2304};
    
    if (harmonyType.contains("minor") || mood == "dark") {
        // Minor chord progression
        int chordRoots[] = {57, 53, 48, 55}; // Am-F-C-G
        int minorChord[] = {0, 3, 7};
        
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 3; j++) {
                pattern.append(QJsonObject{
                    {"start_ticks", chordPositions[i]},
                    {"key", chordRoots[i] + minorChord[j]},
                    {"velocity", mood == "energetic" ? 80 : 70},
                    {"length_ticks", 700}
                });
            }
        }
    } else {
        // Major/uplifting progression
        int chordRoots[] = {48, 53, 57, 55}; // C-F-Am-G
        int majorChord[] = {0, 4, 7};
        
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 3; j++) {
                pattern.append(QJsonObject{
                    {"start_ticks", chordPositions[i]},
                    {"key", chordRoots[i] + majorChord[j]},
                    {"velocity", mood == "uplifting" ? 85 : 75},
                    {"length_ticks", 700}
                });
            }
        }
    }
    
    return pattern;
}

QJsonArray AiAgent::generateAIMelodyPattern(const QString& genre, const QString& mood, int tempo, const QString& key, const QJsonObject& styleChar)
{
    QJsonArray pattern;
    QString soundDesign = styleChar["sound_design"].toString();
    
    qDebug() << "Generating AI melody pattern - Genre:" << genre << "Mood:" << mood << "Sound:" << soundDesign;
    
    if (genre.contains("ambient") || mood == "chill") {
        // Slow, atmospheric melody
        int melodyNotes[] = {72, 74, 76, 74, 72, 69, 67, 69};
        for (int i = 0; i < 8; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", i * 384},
                {"key", melodyNotes[i]},
                {"velocity", 60 + i * 2},
                {"length_ticks", 300}
            });
        }
    } else if (mood == "energetic") {
        // Energetic, rhythmic melody
        int melodyNotes[] = {72, 76, 79, 74, 77, 74, 76, 72};
        for (int i = 0; i < 8; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", i * 192},
                {"key", melodyNotes[i]},
                {"velocity", 85 + (i % 3) * 10},
                {"length_ticks", 150}
            });
        }
    } else {
        // Balanced melody
        int melodyNotes[] = {72, 74, 76, 74, 72, 69, 72, 74};
        for (int i = 0; i < 8; i++) {
            pattern.append(QJsonObject{
                {"start_ticks", i * 240},
                {"key", melodyNotes[i]},
                {"velocity", 75 + (i % 2) * 5},
                {"length_ticks", 200}
            });
        }
    }
    
    return pattern;
}

// =============================================================================
// AI-NATIVE HELPER METHODS - PURE AI ORCHESTRATION
// =============================================================================

QString AiAgent::getOpenAIAPIKey()
{
    // Try environment variable first
    QString apiKey = qgetenv("OPENAI_API_KEY");
    if (!apiKey.isEmpty()) {
        return apiKey;
    }
    
    // Try .envs file in project root
    QFile envFile("/Users/jusung/Desktop/GPT5Hackathon/lmms/.envs");
    if (envFile.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QTextStream in(&envFile);
        while (!in.atEnd()) {
            QString line = in.readLine().trimmed();
            if (line.startsWith("OPENAI_API_KEY=")) {
                return line.mid(15); // Remove "OPENAI_API_KEY="
            }
        }
    }
    
    return QString(); // No API key found
}

QString AiAgent::getLMMSToolsDescription()
{
    return QString(
        "LMMS TOOL CAPABILITIES (exact parameter formats):\n"
        "1. set_tempo: {\"bpm\": 170} - Change project tempo\n"
        "2. create_track: {\"type\": \"instrument\", \"name\": \"Track Name\", \"instrument\": \"TripleOscillator\"} - type must be 'instrument' or 'sample'\n" 
        "3. add_instrument: {\"track\": \"Track Name\", \"instrument\": \"TripleOscillator\"} - Valid: TripleOscillator, DrumSynth, AudioFileProcessor, BitInvader, Organic\n"
        "4. create_midi_clip: {\"track\": \"Track Name\", \"start_ticks\": 0, \"length_ticks\": 3840} - Create MIDI pattern clip\n"
        "5. write_notes: {\"track\": \"Track Name\", \"clip_index\": 0, \"notes\": [{\"key\": 60, \"velocity\": 100, \"start_ticks\": 0, \"length_ticks\": 192}]} - MIDI notes\n"
        "6. add_sample_clip: {\"track\": \"Track Name\", \"file\": \"/path/sample.wav\", \"start_ticks\": 0} - Audio samples\n"
        "7. add_effect: {\"track\": \"Track Name\", \"effect\": \"Compressor\"} - Valid: Compressor, Reverb, Delay, EQ\n"
        "8. move_clip: {\"track\": \"Track Name\", \"clip_index\": 0, \"new_position\": 3840} - Position clips\n"
        "9. duplicate_clip: {\"track\": \"Track Name\", \"clip_index\": 0} - Copy clips\n"
        "10. create_automation_clip: {\"parameter\": \"volume\", \"track\": \"Track Name\", \"start_ticks\": 0} - Automation\n"
        "11. create_section: {\"name\": \"Intro\", \"start_ticks\": 0, \"length_ticks\": 7680} - Arrangement sections\n"
        "12. duplicate_section: {\"section\": \"Intro\"} - Copy sections\n"
        "13. mutate_section: {\"section\": \"Intro\", \"mutations\": [\"transpose\"]} - Modify sections\n"
        "14. sidechain_pump_automation: {\"trigger_track\": \"Kick\", \"target_track\": \"Bass\"} - Sidechain\n"
        "15. quantize_notes: {\"track\": \"Track Name\", \"clip_index\": 0, \"grid\": 192} - Quantize timing\n"
        "16. apply_groove: {\"track\": \"Track Name\", \"clip_index\": 0, \"groove\": \"swing\"} - Apply groove\n"
        "\nALL parameters must use exact formats shown. Use 192 ticks = 1/16 note, 3840 = 4 bars."
    );
}

QString AiAgent::getLMMSInstrumentsDescription()
{
    return QString(
        "AVAILABLE LMMS INSTRUMENTS:\n"
        "• TripleOscillator: Multi-waveform synthesizer (sine, saw, square, triangle)\n"
        "  - Best for: Bass, leads, pads, arps\n"
        "  - Parameters: oscillator types, detuning, volume, filter\n"
        "\n"
        "• DrumSynth: Drum machine synthesizer\n"
        "  - Best for: Electronic drums, percussion\n"
        "  - Parameters: kick, snare, hihat synthesis\n"
        "\n"
        "• AudioFileProcessor: Sample player\n"
        "  - Best for: Drum samples, vocal chops, loops\n"
        "  - Parameters: sample file, pitch, reverse\n"
        "\n"
        "• BitInvader: Wavetable synthesizer\n"
        "  - Best for: Digital leads, aggressive sounds\n"
        "  - Parameters: wavetable selection, interpolation\n"
        "\n"
        "• Organic: Physical modeling synthesizer\n"
        "  - Best for: Realistic instruments, organic textures\n"
        "  - Parameters: wave distortion, harmonics\n"
        "\n"
        "COMMON PRESETS BY GENRE:\n"
        "House: TripleOscillator (saw bass), DrumSynth (909 drums)\n"
        "Trap: AudioFileProcessor (808 samples), TripleOscillator (leads)\n"
        "Ambient: TripleOscillator (pad sounds), Organic (textures)\n"
        "Techno: BitInvader (acid leads), DrumSynth (808 drums)"
    );
}

QJsonObject AiAgent::makeAIAPICallWithRetry(const QString& message, int maxRetries)
{
    qDebug() << "Making AI API call with retry logic, max retries:" << maxRetries;
    
    for (int attempt = 1; attempt <= maxRetries; attempt++) {
        qDebug() << "AI API attempt" << attempt << "of" << maxRetries;
        
        QJsonObject result = makeAIAPICall(message);
        
        if (!result.isEmpty()) {
            qDebug() << "AI API call successful on attempt" << attempt;
            return result;
        }
        
        if (attempt < maxRetries) {
            qDebug() << "AI API attempt" << attempt << "failed, retrying...";
            // Wait briefly before retry (progressive backoff)
            QEventLoop waitLoop;
            QTimer::singleShot(attempt * 1000, &waitLoop, &QEventLoop::quit); // 1s, 2s, 3s delays
            waitLoop.exec();
        }
    }
    
    qDebug() << "All AI API attempts failed. No fallback - as requested by user.";
    return QJsonObject(); // Return empty - no fallbacks allowed
}

QJsonObject AiAgent::processAIOrchestrationResponse(const QJsonObject& aiResponse)
{
    qDebug() << "Processing AI orchestration response";
    
    if (aiResponse.isEmpty()) {
        qDebug() << "Empty AI response - cannot process";
        return QJsonObject();
    }
    
    // Validate the AI response structure
    if (!aiResponse.contains("analysis") || !aiResponse.contains("orchestration_plan")) {
        qDebug() << "Invalid AI response format - missing required fields";
        return QJsonObject();
    }
    
    QJsonObject analysis = aiResponse["analysis"].toObject();
    QJsonArray orchestrationPlan = aiResponse["orchestration_plan"].toArray();
    
    qDebug() << "AI Analysis:";
    qDebug() << "  Musical Style:" << analysis["musical_style"].toString();
    qDebug() << "  Tempo:" << analysis["tempo"].toInt();
    qDebug() << "  Key:" << analysis["key"].toString();
    qDebug() << "  Mood:" << analysis["mood"].toString();
    qDebug() << "  Orchestration steps:" << orchestrationPlan.size();
    
    // Convert AI orchestration plan to our tool sequence format
    QJsonArray toolSequence;
    
    for (const QJsonValue& stepValue : orchestrationPlan) {
        QJsonObject step = stepValue.toObject();
        
        QJsonObject toolCall;
        toolCall["tool"] = step["tool"].toString();
        toolCall["params"] = step["params"].toObject();
        toolCall["reasoning"] = step["reasoning"].toString();
        
        toolSequence.append(toolCall);
    }
    
    // Create result with both analysis and executable sequence
    QJsonObject result;
    result["analysis"] = analysis;
    result["tool_sequence"] = toolSequence;
    result["expected_outcome"] = aiResponse["expected_outcome"].toString();
    result["ai_generated"] = true;
    
    qDebug() << "AI orchestration response processed successfully";
    return result;
}

} // namespace lmms::gui