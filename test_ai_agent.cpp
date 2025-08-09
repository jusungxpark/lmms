#include <iostream>
#include <QApplication>
#include <QMainWindow>
#include <QJsonObject>
#include <QJsonArray>
#include <QJsonDocument>
#include <QDebug>

// Include AI Agent headers
#include "include/AiSidebar.h"
#include "include/AiAgent.h"
#include "src/core/Song.h"
#include "src/core/Engine.h"

using namespace lmms::gui;

class AIAgentTester : public QObject
{
    Q_OBJECT
    
public:
    AIAgentTester(QObject* parent = nullptr) : QObject(parent) {}
    
    bool testNaturalLanguageProcessing()
    {
        qDebug() << "=== Testing Natural Language Processing ===";
        
        AiSidebar sidebar;
        AiAgent agent(&sidebar);
        
        // Test intent recognition
        QStringList testMessages = {
            "create a Fred again style house beat with 128 BPM",
            "make a drum pattern with trap hi-hats",
            "build a full track with bass, drums, and chords",
            "add swing to the drum pattern",
            "quantize the bass to 1/16 notes"
        };
        
        for (const QString& msg : testMessages) {
            qDebug() << "Testing message:" << msg;
            
            // Test parameter extraction
            QJsonObject params = agent.extractMusicalParameters(msg);
            qDebug() << "Extracted parameters:" << QJsonDocument(params).toJson(QJsonDocument::Compact);
            
            // Test musical style analysis  
            if (msg.contains("Fred again")) {
                MusicalPattern pattern = agent.analyzeMusicalStyle("fred again");
                qDebug() << "Genre:" << pattern.genre << "Tempo:" << pattern.tempo;
                if (pattern.genre != "uk_garage" || pattern.tempo != 128) {
                    qDebug() << "ERROR: Fred Again style not recognized correctly";
                    return false;
                }
            }
        }
        
        qDebug() << "Natural Language Processing: PASSED";
        return true;
    }
    
    bool testToolOrchestration()
    {
        qDebug() << "=== Testing Tool Orchestration ===";
        
        AiSidebar sidebar;
        AiAgent agent(&sidebar);
        
        // Test tool sequence planning for Fred Again style
        QJsonObject context;
        context["musical_context"] = QJsonObject{{"tempo", 128}, {"genre", "uk_garage"}};
        
        QJsonArray sequence = agent.planToolSequence("create_fred_again_house_beat", context);
        
        if (sequence.isEmpty()) {
            qDebug() << "ERROR: No tool sequence generated";
            return false;
        }
        
        qDebug() << "Generated tool sequence with" << sequence.size() << "steps";
        
        // Verify sequence contains expected tools
        QStringList expectedTools = {"set_tempo", "create_track", "create_midi_clip", "write_notes", "add_effect"};
        bool foundExpectedTools = false;
        
        for (const QJsonValue& step : sequence) {
            QJsonObject stepObj = step.toObject();
            QString toolName = stepObj["tool"].toString();
            qDebug() << "Step:" << toolName;
            
            if (expectedTools.contains(toolName)) {
                foundExpectedTools = true;
            }
        }
        
        if (!foundExpectedTools) {
            qDebug() << "ERROR: Expected tools not found in sequence";
            return false;
        }
        
        qDebug() << "Tool Orchestration: PASSED";
        return true;
    }
    
    bool testToolImplementations()
    {
        qDebug() << "=== Testing Tool Implementations ===";
        
        AiSidebar sidebar;
        
        // Test basic tool execution
        QJsonObject tempoParams;
        tempoParams["bpm"] = 125;
        
        AiToolResult result = sidebar.runTool("set_tempo", tempoParams);
        if (!result.success) {
            qDebug() << "ERROR: set_tempo tool failed:" << result.output;
            return false;
        }
        
        qDebug() << "set_tempo result:" << result.output;
        
        // Test track creation
        QJsonObject trackParams;
        trackParams["type"] = "instrument";
        trackParams["name"] = "Test Drums";
        trackParams["instrument"] = "kicker";
        
        result = sidebar.runTool("create_track", trackParams);
        if (!result.success) {
            qDebug() << "ERROR: create_track tool failed:" << result.output;
            return false;
        }
        
        qDebug() << "create_track result:" << result.output;
        
        // Test MIDI clip creation
        QJsonObject clipParams;
        clipParams["track_name"] = "Test Drums";
        clipParams["start_ticks"] = 0;
        clipParams["length_ticks"] = 768; // 1 bar
        
        result = sidebar.runTool("create_midi_clip", clipParams);
        if (!result.success) {
            qDebug() << "ERROR: create_midi_clip tool failed:" << result.output;
            return false;
        }
        
        qDebug() << "create_midi_clip result:" << result.output;
        
        // Test note writing
        QJsonArray notes;
        notes.append(QJsonObject{{"start_ticks", 0}, {"key", 36}, {"velocity", 100}, {"length_ticks", 96}});
        notes.append(QJsonObject{{"start_ticks", 384}, {"key", 38}, {"velocity", 100}, {"length_ticks", 96}});
        
        QJsonObject notesParams;
        notesParams["track_name"] = "Test Drums";
        notesParams["clip_index"] = 0;
        notesParams["notes"] = notes;
        
        result = sidebar.runTool("write_notes", notesParams);
        if (!result.success) {
            qDebug() << "ERROR: write_notes tool failed:" << result.output;
            return false;
        }
        
        qDebug() << "write_notes result:" << result.output;
        
        qDebug() << "Tool Implementations: PASSED";
        return true;
    }
    
    bool testParameterValidation()
    {
        qDebug() << "=== Testing Parameter Validation ===";
        
        AiSidebar sidebar;
        AiAgent agent(&sidebar);
        
        // Test tempo validation
        QJsonObject invalidTempo;
        invalidTempo["bpm"] = 300; // Too high
        
        bool isValid = agent.validateParameters(invalidTempo, "set_tempo");
        if (isValid) {
            qDebug() << "ERROR: Invalid tempo was not caught";
            return false;
        }
        
        QJsonObject sanitizedTempo = agent.sanitizeParameters(invalidTempo, "set_tempo");
        int sanitizedBPM = sanitizedTempo["bpm"].toInt();
        if (sanitizedBPM > 200) {
            qDebug() << "ERROR: Tempo not properly sanitized";
            return false;
        }
        
        qDebug() << "Sanitized BPM:" << sanitizedBPM;
        
        // Test note validation
        QJsonArray invalidNotes;
        invalidNotes.append(QJsonObject{{"key", 200}, {"velocity", 150}}); // Invalid values
        
        QJsonObject invalidNotesParams;
        invalidNotesParams["notes"] = invalidNotes;
        
        isValid = agent.validateParameters(invalidNotesParams, "write_notes");
        if (isValid) {
            qDebug() << "ERROR: Invalid notes were not caught";
            return false;
        }
        
        QJsonObject sanitizedNotes = agent.sanitizeParameters(invalidNotesParams, "write_notes");
        QJsonArray sanitizedArray = sanitizedNotes["notes"].toArray();
        QJsonObject firstNote = sanitizedArray[0].toObject();
        
        if (firstNote["key"].toInt() > 127 || firstNote["velocity"].toInt() > 127) {
            qDebug() << "ERROR: Notes not properly sanitized";
            return false;
        }
        
        qDebug() << "Parameter Validation: PASSED";
        return true;
    }
    
    bool testMusicTheory()
    {
        qDebug() << "=== Testing Music Theory Engine ===";
        
        AiSidebar sidebar;
        AiAgent agent(&sidebar);
        
        // Test scale generation
        QStringList cMajorScale = agent.getScaleNotes("c", "major");
        QStringList expectedScale = {"C", "D", "E", "F", "G", "A", "B"};
        
        if (cMajorScale != expectedScale) {
            qDebug() << "ERROR: C Major scale incorrect";
            qDebug() << "Expected:" << expectedScale;
            qDebug() << "Got:" << cMajorScale;
            return false;
        }
        
        // Test BPM for genres
        int houseBPM = agent.getBPMForGenre("house");
        if (houseBPM != 126) {
            qDebug() << "ERROR: House BPM incorrect, expected 126, got" << houseBPM;
            return false;
        }
        
        // Test musical pattern analysis
        MusicalPattern pattern = agent.analyzeMusicalStyle("house");
        if (pattern.genre != "house" || pattern.tempo != 126) {
            qDebug() << "ERROR: House pattern analysis incorrect";
            return false;
        }
        
        qDebug() << "Music Theory Engine: PASSED";
        return true;
    }
    
    void runAllTests()
    {
        qDebug() << "Starting AI Agent Comprehensive Testing...";
        qDebug() << "==========================================";
        
        bool allPassed = true;
        
        allPassed &= testNaturalLanguageProcessing();
        allPassed &= testToolOrchestration();  
        allPassed &= testToolImplementations();
        allPassed &= testParameterValidation();
        allPassed &= testMusicTheory();
        
        qDebug() << "==========================================";
        if (allPassed) {
            qDebug() << "ALL TESTS PASSED! AI Agent is fully functional.";
        } else {
            qDebug() << "SOME TESTS FAILED! Please review issues above.";
        }
        qDebug() << "==========================================";
        
        QApplication::quit();
    }
};

#include "test_ai_agent.moc"

int main(int argc, char** argv)
{
    QApplication app(argc, argv);
    
    // Initialize LMMS engine
    Engine::init();
    
    AIAgentTester tester;
    
    // Run tests after event loop starts
    QTimer::singleShot(100, &tester, &AIAgentTester::runAllTests);
    
    return app.exec();
}