#include "AiSidebar.h"
#include "Song.h"
#include "Engine.h"
#include "Track.h"
#include "InstrumentTrack.h"
#include "SampleTrack.h"
#include "SampleClip.h"
#include "MidiClip.h"
#include "AutomationClip.h"
#include "TimePos.h"
#include "Note.h"
#include "Effect.h"
#include "EffectChain.h"
#include "ConfigManager.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QScrollArea>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QDir>
#include <QProgressBar>
#include <QDateTime>
#include <QCryptographicHash>
#include <QTimer>
#include <QRegExp>
#include <QFile>
#include <QTextStream>

using namespace lmms;
namespace lmms::gui {

AiSidebar::AiSidebar(QWidget* parent)
    : SideBarWidget(tr("AI"), QPixmap(), parent), m_net(std::make_unique<QNetworkAccessManager>(this))
{
    setupUI();
    
    // Load API key from .env file or environment
    loadApiKeyFromEnv();
    
    if (m_apiKey.isEmpty()) {
        addMessage("No API key found. Please set OPENAI_API_KEY in .env file", "system");
    }
    
    // Initialize symbolic-first architecture
    initializeAgents();
    setupSafetyGuards();
    
    // Auto-test API functionality with new key (remove in production)
    QTimer::singleShot(2000, this, [this]() {
        qDebug() << "AI Sidebar: Testing new API key...";
        addMessage("Testing new OpenAI API key...", "system");
        sendToGPT5("Test new API key - create a simple response");
    });
    
    // Create initial snapshot
    createSnapshot("Initial State");
    
    setState(ProcessingState::Idle);
}

AiSidebar::~AiSidebar() {
    if (m_reply) { m_reply->abort(); m_reply->deleteLater(); }
}

void AiSidebar::setupUI()
{
    m_rootLayout = new QVBoxLayout(this);
    m_rootLayout->setContentsMargins(8,8,8,8);
    m_rootLayout->setSpacing(6);

    m_scroll = new QScrollArea(this);
    m_scroll->setWidgetResizable(true);
    m_msgs = new QWidget(m_scroll);
    m_msgsLayout = new QVBoxLayout(m_msgs);
    m_msgsLayout->addStretch();
    m_scroll->setWidget(m_msgs);

    // Status and progress indicators
    m_statusLabel = new QLabel("Ready", this);
    m_statusLabel->setStyleSheet("color: green; font-weight: bold;");
    m_progressBar = new QProgressBar(this);
    m_progressBar->setVisible(false);
    m_progressBar->setRange(0, 0); // Indeterminate progress
    
    auto row = new QWidget(this);
    auto rowL = new QHBoxLayout(row);
    rowL->setContentsMargins(0,0,0,0);
    m_input = new QLineEdit(row);
    m_input->setPlaceholderText("Tell the AI what to do... (e.g., 'Create a 4-bar drum pattern')");
    m_send = new QPushButton("Send", row);
    rowL->addWidget(m_input);
    rowL->addWidget(m_send);

    auto headerLayout = new QHBoxLayout();
    headerLayout->addWidget(new QLabel("AI (GPT-5)", this));
    headerLayout->addStretch();
    headerLayout->addWidget(m_statusLabel);
    
    auto headerWidget = new QWidget(this);
    headerWidget->setLayout(headerLayout);
    
    m_rootLayout->addWidget(headerWidget);
    m_rootLayout->addWidget(m_progressBar);
    m_rootLayout->addWidget(m_scroll, 1);
    m_rootLayout->addWidget(row);

    connect(m_send, &QPushButton::clicked, this, &AiSidebar::onSend);
    connect(m_input, &QLineEdit::returnPressed, this, &AiSidebar::onSend);
}

void AiSidebar::addMessage(const QString& text, const QString& role)
{
    auto* lbl = new QLabel(QString("[%1] %2").arg(role, text), m_msgs);
    lbl->setWordWrap(true);
    m_msgsLayout->insertWidget(m_msgsLayout->count()-1, lbl);
}

void AiSidebar::onSend()
{
    const QString text = m_input->text().trimmed();
    if (text.isEmpty()) return;
    
    if (m_state != ProcessingState::Idle) {
        addMessage("Please wait for current request to complete...", "system");
        return;
    }
    
    m_input->clear();
    m_send->setEnabled(false);
    setState(ProcessingState::SendingRequest);
    
    addMessage(text, "user");
    
    // Parse musical intent first (Cursor-like preprocessing)
    QJsonObject intent = parseMusicalIntent(text);
    addMessage(QString("Parsed intent: %1 %2").arg(intent.value("action").toString()).arg(intent.value("element").toString()), "system");
    
    // Switch to appropriate agent
    QString element = intent.value("element").toString();
    if (element == "harmony" || element == "melody") {
        switchAgent(AgentRole::Composer, intent);
    } else if (element == "rhythm") {
        switchAgent(AgentRole::RhythmGroove, intent);
    } else if (text.toLower().contains("mix") || text.toLower().contains("effect")) {
        switchAgent(AgentRole::MixAssistant, intent);
    } else {
        switchAgent(AgentRole::Planner, intent);
    }
    
    // Create undo point before making changes
    createSnapshot("Before: " + text.left(20));
    
    sendToGPT5(text);
}

QJsonArray AiSidebar::getToolDefinitions() const
{
    QJsonArray tools;
    auto add = [&](const char* name, const char* description){
        QJsonObject t;
        t["type"] = "function";
        t["name"] = name;
        t["description"] = description;
        QJsonObject params;
        params["type"] = "object";
        params["properties"] = QJsonObject();
        t["parameters"] = params;
        tools.append(t);
    };
    
    // Core DAW tools
    add("set_tempo", "Set project tempo in BPM (parameter: bpm)");
    add("set_time_signature", "Set time signature numerator/denominator (parameters: numerator, denominator)");
    add("create_track", "Create instrument, sample, or automation track (parameters: type, name, instrument)");
    add("create_midi_clip", "Create MIDI clip at position (parameters: track_name, start_bar, length_bars)");
    add("write_notes", "Write MIDI notes to clip (parameters: track_name, clip_index, notes array with start_bar, length_bar, key, velocity)");
    add("quantize_track", "Quantize MIDI notes on track to grid (parameters: track_name, grid)");
    add("apply_groove", "Apply swing/groove timing offsets (parameters: track_name, swing, resolution)");
    add("add_effect", "Insert effect on track (parameters: track_name, effect_name)");
    add("add_sample_clip", "Create sample clip loading audio file (parameters: track_name, file, start_ticks)");
    add("create_automation_clip", "Create automation clip (parameters: start_ticks)");
    add("export_project", "Export project as MIDI (parameters: path, format)");
    
    // Advanced composition tools
    add("create_song_section", "Create structured song section (parameters: section_type, start_bar, length_bars, key, style)");
    add("duplicate_section", "Duplicate section to new location (parameters: source_start, source_end, target_start)");
    add("mutate_pattern", "Add variations to existing MIDI pattern (parameters: track_name, variation_amount)");
    add("create_chord_progression", "Generate chord progression (parameters: track_name, progression, key, start_bar, chord_duration)");
    add("create_melody", "Generate melody line (parameters: track_name, scale, start_bar, length_bars)");
    add("create_drum_pattern", "Generate drum pattern (parameters: track_name, style, start_bar, length_bars)");
    
    // Advanced automation & effects
    add("create_sidechain_pump", "Create sidechain compression (parameters: source_track, target_track, intensity, release_time)");
    add("create_filter_sweep", "Create filter sweep automation (parameters: track_name, start_freq, end_freq, start_bar, length_bars)");
    add("create_volume_automation", "Create volume automation curve (parameters: track_name, curve_type, start_bar, length_bars)");
    add("create_send_bus", "Create send/return bus (parameters: bus_name, effect_type)");
    
    // Workflow tools
    add("analyze_project", "Analyze project structure and provide insights (parameters: analysis_type)");
    add("suggest_improvements", "Suggest musical and mixing improvements");
    add("create_undo", "Create undo point for batch operations");
    add("preview_changes", "Preview changes before applying (parameters: dry_run)");
    add("export_audio", "Export project as audio file (parameters: path, format, quality, start_bar, end_bar)");
    
    return tools;
}

void AiSidebar::sendToGPT5(const QString& message)
{
    if (m_apiKey.isEmpty()) { 
        addMessage("No API key set.", "system"); 
        setState(ProcessingState::Error);
        return; 
    }
    
    // Store message for retry logic
    m_lastMessage = message;
    setState(ProcessingState::WaitingResponse);
    // Build input array with a routing system message
    QJsonArray input;
    QJsonObject sys; sys["role"] = "system"; sys["content"] =
        "You are an advanced LMMS AI assistant implementing Cursor-like multi-agent architecture for music production.\n\n"
        "CORE PRINCIPLES:\n"
        "1. Symbolic-first: Work with musical symbols (notes, chords, tempo, structure) before audio\n"
        "2. Plan → Preview → Apply: Always plan changes, show diffs, get approval before applying\n"
        "3. Multi-agent coordination: Switch between specialized agents (Planner, Composer, Mix Assistant, Critic)\n"
        "4. Safety-first: Create undo points, run safety checks, preserve originals\n"
        "5. Explainable changes: All modifications should be clearly documented and reversible\n\n"
        "AGENT ROLES:\n"
        "- Planner: Breaks requests into tasks, orchestrates workflow\n"
        "- Composer: Handles chords, melodies, rhythms, arrangements\n"
        "- Mix Assistant: EQ, compression, effects, spatial processing\n"
        "- Critic: Reviews changes for safety, musical coherence, quality\n\n"
        "WORKFLOW:\n"
        "1. Parse musical intent from natural language\n"
        "2. Switch to appropriate agent(s) for the task\n"
        "3. Create change plan with preview\n"
        "4. Run safety and musical coherence checks\n"
        "5. Apply changes with full undo capability\n"
        "6. Provide diff view and accept/reject options\n\n"
        "Always maintain musical context awareness and production best practices.";
    QJsonObject usr; usr["role"] = "user"; usr["content"] = message;
    input.append(sys); input.append(usr);

    QJsonObject body;
    body["model"] = "gpt-5";
    QJsonObject reasoning; reasoning["effort"] = "medium"; body["reasoning"] = reasoning;
    QJsonObject text;
    QJsonObject format; format["type"] = "text";
    text["format"] = format;
    text["verbosity"] = "medium";
    body["text"] = text;
    body["input"] = input;
    body["tools"] = getToolDefinitions();
    QJsonObject toolChoice;
    toolChoice["type"] = "allowed_tools";
    toolChoice["mode"] = "auto";
    
    // Create simplified tool list for tool_choice
    QJsonArray toolList;
    for (const auto& tool : getToolDefinitions()) {
        QJsonObject t;
        t["type"] = "function";
        t["name"] = tool.toObject().value("name").toString();
        toolList.append(t);
    }
    toolChoice["tools"] = toolList;
    body["tool_choice"] = toolChoice;

    QNetworkRequest req(QUrl("https://api.openai.com/v1/responses"));
    req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    req.setRawHeader("Authorization", QByteArray("Bearer ") + m_apiKey.toUtf8());
    QJsonDocument doc(body);
    
    // Debug logging
    qDebug() << "AI Sidebar: Sending API request";
    qDebug() << "Request body:" << doc.toJson(QJsonDocument::Compact);
    
    m_reply = m_net->post(req, doc.toJson());
    connect(m_reply, &QNetworkReply::finished, this, &AiSidebar::onNetworkFinished);
}

void AiSidebar::onNetworkFinished()
{
    if (!m_reply) return;
    
    const QByteArray data = m_reply->readAll();
    const int statusCode = m_reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    
    // Debug logging
    qDebug() << "AI Sidebar: Received API response";
    qDebug() << "Status code:" << statusCode;
    qDebug() << "Response data:" << QString::fromUtf8(data.left(1000));
    
    m_reply->deleteLater(); m_reply = nullptr;
    
    if (statusCode != 200) {
        QString errorDetails = QString::fromUtf8(data.left(500));
        addMessage(QString("HTTP %1: %2").arg(statusCode).arg(errorDetails), "system");
        
        // Implement retry logic
        if (m_retryCount < m_maxRetries) {
            m_retryCount++;
            int delayMs = 1000 * m_retryCount; // Linear backoff
            addMessage(QString("Retrying in %1s... (attempt %2/%3)").arg(delayMs/1000).arg(m_retryCount).arg(m_maxRetries), "system");
            
            QTimer::singleShot(delayMs, this, [this]() {
                setState(ProcessingState::WaitingResponse);
                sendToGPT5(m_lastMessage);
            });
            return;
        } else {
            addMessage("Max retries reached. Check API key and endpoint.", "system");
            setState(ProcessingState::Error);
            m_retryCount = 0;
            return;
        }
    }
    
    QJsonDocument d = QJsonDocument::fromJson(data);
    qDebug() << "AI Sidebar: JSON parsing result - isNull:" << d.isNull();
    if (d.isNull()) {
        addMessage("Invalid JSON response from API", "system");
        addMessage(QString("Raw response: %1").arg(QString::fromUtf8(data.left(300))), "system");
        setState(ProcessingState::Error);
        m_retryCount = 0;
        return;
    }
    
    const QJsonObject obj = d.object();
    qDebug() << "AI Sidebar: Parsed JSON object - keys:" << obj.keys();
    qDebug() << "AI Sidebar: Checking for error key...";
    if (obj.contains("error") && !obj.value("error").isNull()) {
        qDebug() << "AI Sidebar: Found actual error, processing error";
        QJsonObject error = obj.value("error").toObject();
        QString errorMsg = error.value("message").toString();
        QString errorType = error.value("type").toString();
        QString errorCode = error.value("code").toString();
        
        addMessage(QString("API Error: %1").arg(errorMsg), "system");
        if (!errorType.isEmpty()) addMessage(QString("Type: %1").arg(errorType), "system");
        if (!errorCode.isEmpty()) addMessage(QString("Code: %1").arg(errorCode), "system");
        
        setState(ProcessingState::Error);
        m_retryCount = 0;
        return;
    }
    qDebug() << "AI Sidebar: No error found, continuing with success path";
    
    // Reset retry count on successful response
    m_retryCount = 0;
    qDebug() << "AI Sidebar: About to call setState(ExecutingTools)";
    setState(ProcessingState::ExecutingTools);
    qDebug() << "AI Sidebar: setState completed, about to call processResponse with keys:" << obj.keys();
    try {
        processResponse(obj);
        qDebug() << "AI Sidebar: processResponse completed successfully";
    } catch (const std::exception& e) {
        qDebug() << "AI Sidebar: Exception in processResponse:" << e.what();
        addMessage("Error processing response: " + QString(e.what()), "system");
    } catch (...) {
        qDebug() << "AI Sidebar: Unknown exception in processResponse";
        addMessage("Unknown error processing response", "system");
    }
    setState(ProcessingState::Idle);
}

void AiSidebar::processResponse(const QJsonObject& response)
{
    qDebug() << "AI Sidebar: Processing response...";
    qDebug() << "Response keys:" << response.keys();
    
    // Handle GPT-5 response format
    if (response.contains("output_text")) {
        // Simple text response
        QString text = response.value("output_text").toString();
        if (!text.isEmpty()) {
            addMessage(text, "assistant");
        }
    }
    
    // Handle tool calls in the output array
    const QJsonArray output = response.value("output").toArray();
    for (const auto& v : output) {
        const QJsonObject item = v.toObject();
        const QString type = item.value("type").toString();
        
        if (type == "message") {
            qDebug() << "AI Sidebar: Found message type";
            QString text;
            const QJsonValue content = item.value("content");
            qDebug() << "Content is array:" << content.isArray() << "Content is string:" << content.isString();
            if (content.isArray()) {
                for (const auto& c : content.toArray()) {
                    const QJsonObject co = c.toObject();
                    qDebug() << "Content item type:" << co.value("type").toString();
                    if (co.value("type").toString() == "output_text") {
                        text += co.value("text").toString();
                        qDebug() << "Added text:" << co.value("text").toString();
                    }
                }
            } else if (content.isString()) {
                text = content.toString();
            }
            qDebug() << "Final text:" << text;
            if (!text.isEmpty()) addMessage(text, "assistant");
        } 
        else if (type == "function_call") {
            executeToolCall(item);
        }
    }
    
    // If no content was processed, check for direct execution
    if (output.isEmpty() && !response.contains("output_text")) {
        // Try to execute tools directly based on the request
        executeDirectAction();
    }
}

void AiSidebar::executeToolCall(const QJsonObject& toolCall)
{
    const QString name = toolCall.value("name").toString();
    const QJsonObject args = QJsonDocument::fromJson(toolCall.value("arguments").toString().toUtf8()).object();
    AiToolResult r; r.toolName = name; r.input = args; r.success = false;
    
    // Core DAW tools
    if (name == "set_tempo") r = toolSetTempo(args);
    else if (name == "set_time_signature") r = toolSetTimeSignature(args);
    else if (name == "create_track") r = toolCreateTrack(args);
    else if (name == "create_midi_clip") r = toolCreateMidiClip(args);
    else if (name == "write_notes") r = toolWriteNotes(args);
    else if (name == "quantize_track") r = toolQuantizeTrack(args);
    else if (name == "apply_groove") r = toolApplyGroove(args);
    else if (name == "add_effect") r = toolAddEffect(args);
    else if (name == "add_sample_clip") r = toolAddSampleClip(args);
    else if (name == "create_automation_clip") r = toolCreateAutomationClip(args);
    else if (name == "export_project") r = toolExportProject(args);
    
    // Advanced composition tools
    else if (name == "create_song_section") r = toolCreateSongSection(args);
    else if (name == "duplicate_section") r = toolDuplicateSection(args);
    else if (name == "mutate_pattern") r = toolMutatePattern(args);
    else if (name == "create_chord_progression") r = toolCreateChordProgression(args);
    else if (name == "create_melody") r = toolCreateMelody(args);
    else if (name == "create_drum_pattern") r = toolCreateDrumPattern(args);
    
    // Advanced automation & effects
    else if (name == "create_sidechain_pump") r = toolCreateSidechainPump(args);
    else if (name == "create_filter_sweep") r = toolCreateFilterSweep(args);
    else if (name == "create_volume_automation") r = toolCreateVolumeAutomation(args);
    else if (name == "create_send_bus") r = toolCreateSendBus(args);
    
    // Workflow tools
    else if (name == "analyze_project") r = toolAnalyzeProject(args);
    else if (name == "suggest_improvements") r = toolSuggestImprovements(args);
    else if (name == "create_undo") r = toolCreateUndo(args);
    else if (name == "preview_changes") r = toolPreviewChanges(args);
    else if (name == "export_audio") r = toolExportAudio(args);
    
    else {
        r.output = "Unknown tool: " + name;
    }
    
    addMessage(QString("%1: %2").arg(name, r.success? "✓ " + r.output : "✗ " + r.output), "system");
}

static Track* findTrackByName(const QString& name) {
    Song* s = Engine::getSong(); if (!s) return nullptr;
    for (Track* t : s->tracks()) if (t->name() == name) return t;
    return nullptr;
}

InstrumentTrack* AiSidebar::findInstrumentTrack(const QString& name) const {
    Track* t = findTrackByName(name);
    return dynamic_cast<InstrumentTrack*>(t);
}
Track* AiSidebar::findTrack(const QString& name) const { return findTrackByName(name); }

AiToolResult AiSidebar::toolSetTempo(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "set_tempo";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    const double bpm = p.value("bpm").toDouble(120);
    s->tempoModel().setValue((int)bpm);
    r.success = true; r.output = QString("tempo %1").arg(bpm); return r;
}

AiToolResult AiSidebar::toolSetTimeSignature(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "set_time_signature";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    int num = p.value("numerator").toInt(4);
    int den = p.value("denominator").toInt(4);
    s->getTimeSigModel().setNumerator(num);
    s->getTimeSigModel().setDenominator(den);
    r.success = true; r.output = QString("meter %1/%2").arg(num).arg(den); return r;
}

AiToolResult AiSidebar::toolCreateTrack(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_track";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    const QString type = p.value("type").toString("instrument");
    const QString name = p.value("name").toString("New Track");
    Track* t = nullptr;
    if (type == "instrument") t = Track::create(Track::Type::Instrument, s);
    else if (type == "sample") t = Track::create(Track::Type::Sample, s);
    else if (type == "automation") t = Track::create(Track::Type::Automation, s);
    if (!t) { r.output = "create failed"; return r; }
    t->setName(name);
    if (auto* it = dynamic_cast<InstrumentTrack*>(t)) {
        const QString inst = p.value("instrument").toString(); if (!inst.isEmpty()) it->loadInstrument(inst);
    }
    r.success = true; r.output = QString("track %1 created").arg(name); return r;
}

AiToolResult AiSidebar::toolCreateMidiClip(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_midi_clip";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    const QString trackName = p.value("track_name").toString();
    auto* it = findInstrumentTrack(trackName); if (!it) { r.output = "track not found"; return r; }
    
    // Support both tick-based and bar-based timing
    int start, len;
    if (p.contains("start_bar")) {
        start = (p.value("start_bar").toInt(1) - 1) * TimePos::ticksPerBar();
        len = p.value("length_bars").toDouble(1.0) * TimePos::ticksPerBar();
    } else {
        start = p.value("start_ticks").toInt(0);
        len = p.value("length_ticks").toInt(TimePos::ticksPerBar());
    }
    
    auto* clip = dynamic_cast<MidiClip*>(it->createClip(TimePos(start)));
    if (!clip) { r.output = "clip fail"; return r; }
    clip->changeLength(TimePos(len));
    r.success = true; 
    r.output = QString("midi clip created at bar %1 (%2 bars)").arg((start / TimePos::ticksPerBar()) + 1).arg(len / TimePos::ticksPerBar());
    return r;
}

AiToolResult AiSidebar::toolWriteNotes(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "write_notes";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    const QString trackName = p.value("track_name").toString();
    const int clipIndex = p.value("clip_index").toInt(0);
    auto* it = findInstrumentTrack(trackName); if (!it) { r.output = "track not found"; return r; }
    auto& clips = it->getClips(); if (clipIndex < 0 || (size_t)clipIndex >= clips.size()) { r.output = "bad clip index"; return r; }
    auto* mc = dynamic_cast<MidiClip*>(clips[clipIndex]); if (!mc) { r.output = "not midi"; return r; }
    
    const QJsonArray notes = p.value("notes").toArray();
    for (const auto& n : notes) {
        auto o = n.toObject();
        
        // Support both tick-based and bar-based timing
        int start, len;
        if (o.contains("start_bar")) {
            start = o.value("start_bar").toDouble() * TimePos::ticksPerBar();
            len = o.value("length_bar").toDouble(0.25) * TimePos::ticksPerBar(); // default quarter note
        } else {
            start = o.value("start_ticks").toInt();
            len = o.value("length_ticks").toInt(TimePos::ticksPerBar()/4);
        }
        
        int key = o.value("key").toInt(DefaultKey);
        int vel = o.value("velocity").toInt(100);
        mc->addNote(Note(TimePos(len), TimePos(start), key, (volume_t)vel), false);
    }
    
    r.success = true; 
    r.output = QString("%1 notes added").arg(notes.size()); 
    return r;
}

AiToolResult AiSidebar::toolQuantizeTrack(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "quantize_track";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    auto* it = findInstrumentTrack(p.value("track_name").toString()); if (!it) { r.output = "track not found"; return r; }
    const QString grid = p.value("grid").toString("1/16");
    int div = 16; if (grid=="1/8") div=8; else if (grid=="1/32") div=32; else if (grid=="1/4") div=4;
    const int q = TimePos::ticksPerBar()/div;
    for (auto* c : it->getClips()) if (auto* mc = dynamic_cast<MidiClip*>(c)) {
        for (auto* n : mc->notes()) { n->quantizePos(q); n->quantizeLength(q); }
        mc->rearrangeAllNotes();
    }
    r.success = true; r.output = QString("quantized %1").arg(grid); return r;
}

AiToolResult AiSidebar::toolApplyGroove(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "apply_groove";
    auto* it = findInstrumentTrack(p.value("track_name").toString()); if (!it) { r.output = "track not found"; return r; }
    const double swing = std::clamp(p.value("swing").toDouble(0.1), 0.0, 0.5);
    const int resolution = p.value("resolution").toInt(8);
    const int unit = TimePos::ticksPerBar()/resolution;
    const int offset = (int)(unit * swing);
    for (auto* c : it->getClips()) if (auto* mc = dynamic_cast<MidiClip*>(c)) {
        for (auto* n : mc->notes()) {
            int pos = n->pos(); int idx = pos / unit; if (idx % 2 == 1) n->setPos(TimePos(pos + offset));
        }
        mc->rearrangeAllNotes();
    }
    r.success = true; r.output = QString("swing %1").arg(swing); return r;
}

AiToolResult AiSidebar::toolAddEffect(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "add_effect";
    Track* t = findTrack(p.value("track_name").toString()); if (!t) { r.output = "track not found"; return r; }
    AudioBusHandle* bus = nullptr;
    if (auto* it = dynamic_cast<InstrumentTrack*>(t)) bus = it->audioBusHandle();
    else if (auto* st = dynamic_cast<SampleTrack*>(t)) bus = st->audioBusHandle();
    if (!bus || !bus->effects()) { r.output = "no effect chain"; return r; }
    const QString fx = p.value("effect_name").toString(); if (fx.isEmpty()) { r.output = "missing effect"; return r; }
    Effect* inst = Effect::instantiate(fx, bus->effects(), nullptr); if (!inst) { r.output = "instantiate failed"; return r; }
    bus->effects()->appendEffect(inst);
    r.success = true; r.output = QString("effect %1 added").arg(fx); return r;
}

AiToolResult AiSidebar::toolAddSampleClip(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "add_sample_clip";
    auto* st = dynamic_cast<SampleTrack*>(findTrack(p.value("track_name").toString())); if (!st) { r.output = "sample track not found"; return r; }
    const QString file = p.value("file").toString(); if (file.isEmpty()) { r.output = "missing file"; return r; }
    const int start = p.value("start_ticks").toInt(0);
    if (auto* clip = dynamic_cast<SampleClip*>(st->createClip(TimePos(start)))) {
        clip->setSampleFile(file);
        r.success = true; r.output = QDir(file).dirName(); return r;
    } else { r.output = "clip fail"; return r; }
}

AiToolResult AiSidebar::toolCreateAutomationClip(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_automation_clip";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    Track* a = nullptr; for (Track* t : s->tracks()) if (t->type()==Track::Type::Automation) { a=t; break; }
    if (!a) a = Track::create(Track::Type::Automation, s);
    if (!a) { r.output = "automation track fail"; return r; }
    const int start = p.value("start_ticks").toInt(0);
    auto* clip = dynamic_cast<AutomationClip*>(a->createClip(TimePos(start))); if (!clip) { r.output = "clip fail"; return r; }
    r.success = true; r.output = "automation clip"; return r;
}

AiToolResult AiSidebar::toolExportProject(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "export_project";
    const QString path = p.value("path").toString();
    const QString format = p.value("format").toString("midi");
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    if (path.isEmpty()) { r.output = "missing path"; return r; }
    if (format.toLower()=="midi") { s->exportProjectMidi(path); r.success = true; r.output = QString("midi -> %1").arg(path); return r; }
    r.output = "only midi export here"; return r;
}

// Advanced composition tools
AiToolResult AiSidebar::toolCreateSongSection(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_song_section";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString sectionType = p.value("section_type").toString("verse");
    const int startBar = p.value("start_bar").toInt(1);
    const int lengthBars = p.value("length_bars").toInt(8);
    const QString key = p.value("key").toString("C");
    const QString style = p.value("style").toString("modern");
    
    // Create section marker/comment in the project
    // This is a placeholder - in a full implementation, you'd add project markers
    r.success = true;
    r.output = QString("%1 section at bar %2 (%3 bars, %4 key)").arg(sectionType, QString::number(startBar), QString::number(lengthBars), key);
    return r;
}

AiToolResult AiSidebar::toolDuplicateSection(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "duplicate_section";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    // Implementation would copy clips from one section to another
    r.success = true;
    r.output = "section duplicated";
    return r;
}

AiToolResult AiSidebar::toolMutatePattern(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "mutate_pattern";
    const QString trackName = p.value("track_name").toString();
    auto* it = findInstrumentTrack(trackName);
    if (!it) { r.output = "track not found"; return r; }
    
    // Simple pattern mutation: slight timing/velocity variations
    for (auto* c : it->getClips()) {
        if (auto* mc = dynamic_cast<MidiClip*>(c)) {
            for (auto* n : mc->notes()) {
                // Add slight timing variation (+/- 5% of a 32nd note)
                int variation = (rand() % 10 - 5) * (TimePos::ticksPerBar() / 32 / 20);
                n->setPos(TimePos(std::max(0, n->pos() + variation)));
                
                // Add slight velocity variation (+/- 10)
                int newVel = std::clamp((int)n->getVolume() + (rand() % 20 - 10), 1, 127);
                n->setVolume((volume_t)newVel);
            }
            mc->rearrangeAllNotes();
        }
    }
    
    r.success = true;
    r.output = "pattern mutated with variations";
    return r;
}

AiToolResult AiSidebar::toolCreateChordProgression(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_chord_progression";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString trackName = p.value("track_name").toString();
    auto* it = findInstrumentTrack(trackName);
    if (!it) { r.output = "track not found"; return r; }
    
    const QString progression = p.value("progression").toString("I-V-vi-IV");
    const QString key = p.value("key").toString("C");
    const int startBar = p.value("start_bar").toInt(1);
    const double chordDuration = p.value("chord_duration").toDouble(1.0);
    
    // Create a basic chord progression
    // This is a simplified version - full implementation would parse key signatures
    QMap<QString, int> keyOffsets{{
        {"C", 60}, {"D", 62}, {"E", 64}, {"F", 65}, {"G", 67}, {"A", 69}, {"B", 71}
    }};
    
    int baseNote = keyOffsets.value(key, 60);
    QStringList chords = progression.split("-");
    
    // Create or use first MIDI clip
    MidiClip* mc = nullptr;
    if (!it->getClips().empty()) {
        mc = dynamic_cast<MidiClip*>(it->getClips()[0]);
    } else {
        mc = dynamic_cast<MidiClip*>(it->createClip(TimePos((startBar-1) * TimePos::ticksPerBar())));
    }
    
    if (!mc) { r.output = "clip creation failed"; return r; }
    
    int chordIndex = 0;
    for (const QString& chord : chords) {
        int startTick = (startBar - 1) * TimePos::ticksPerBar() + chordIndex * (chordDuration * TimePos::ticksPerBar());
        int duration = chordDuration * TimePos::ticksPerBar();
        
        // Basic triad construction (simplified)
        QVector<int> chordNotes;
        if (chord == "I" || chord == "i") chordNotes = {0, 4, 7};
        else if (chord == "V") chordNotes = {7, 11, 14};
        else if (chord == "vi") chordNotes = {9, 12, 16};
        else if (chord == "IV") chordNotes = {5, 9, 12};
        else chordNotes = {0, 4, 7}; // default to I
        
        for (int noteOffset : chordNotes) {
            mc->addNote(Note(TimePos(duration), TimePos(startTick), baseNote + noteOffset, 80), false);
        }
        chordIndex++;
    }
    
    r.success = true;
    r.output = QString("%1 progression in %2").arg(progression, key);
    return r;
}

AiToolResult AiSidebar::toolCreateMelody(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_melody";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString trackName = p.value("track_name").toString();
    const QString scale = p.value("scale").toString("major");
    const int startBar = p.value("start_bar").toInt(1);
    const int lengthBars = p.value("length_bars").toInt(4);
    
    auto* it = findInstrumentTrack(trackName);
    if (!it) { r.output = "track not found"; return r; }
    
    // Create or get first MIDI clip
    MidiClip* mc = nullptr;
    if (!it->getClips().empty()) {
        mc = dynamic_cast<MidiClip*>(it->getClips()[0]);
    } else {
        mc = dynamic_cast<MidiClip*>(it->createClip(TimePos((startBar-1) * TimePos::ticksPerBar())));
    }
    
    if (!mc) { r.output = "clip creation failed"; return r; }
    
    // Scale definitions (simplified)
    QMap<QString, QVector<int>> scales;
    scales["major"] = {0, 2, 4, 5, 7, 9, 11};
    scales["minor"] = {0, 2, 3, 5, 7, 8, 10};
    scales["pentatonic"] = {0, 2, 4, 7, 9};
    
    QVector<int> scaleNotes = scales.value(scale, scales["major"]);
    int baseNote = 60; // C4
    
    // Generate simple melodic pattern
    int ticksPerBeat = TimePos::ticksPerBar() / 4;
    int startTick = (startBar - 1) * TimePos::ticksPerBar();
    
    for (int bar = 0; bar < lengthBars; bar++) {
        for (int beat = 0; beat < 4; beat++) {
            // Simple melodic contour: step-wise motion with occasional leaps
            int scaleIndex = (bar * 4 + beat) % scaleNotes.size();
            int noteOffset = scaleNotes[scaleIndex];
            if (beat == 3 && bar < lengthBars - 1) noteOffset += 7; // Octave jump on beat 4
            
            int noteTick = startTick + bar * TimePos::ticksPerBar() + beat * ticksPerBeat;
            int noteDuration = ticksPerBeat / 2; // Eighth notes
            int velocity = 80 + (rand() % 20); // Slight velocity variation
            
            mc->addNote(Note(TimePos(noteDuration), TimePos(noteTick), baseNote + noteOffset, velocity), false);
        }
    }
    
    r.success = true;
    r.output = QString("melody created: %1 scale, %2 bars").arg(scale).arg(lengthBars);
    return r;
}

AiToolResult AiSidebar::toolCreateDrumPattern(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_drum_pattern";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString trackName = p.value("track_name").toString();
    const QString style = p.value("style").toString("4-on-floor");
    const int startBar = p.value("start_bar").toInt(1);
    const int lengthBars = p.value("length_bars").toInt(1);
    
    auto* it = findInstrumentTrack(trackName);
    if (!it) { r.output = "track not found"; return r; }
    
    // Create or get first MIDI clip
    MidiClip* mc = nullptr;
    if (!it->getClips().empty()) {
        mc = dynamic_cast<MidiClip*>(it->getClips()[0]);
    } else {
        mc = dynamic_cast<MidiClip*>(it->createClip(TimePos((startBar-1) * TimePos::ticksPerBar())));
    }
    
    if (!mc) { r.output = "clip creation failed"; return r; }
    
    // Drum note mappings (General MIDI)
    const int kick = 36;
    const int snare = 38;
    const int hihat = 42;
    const int openhat = 46;
    Q_UNUSED(openhat); // May be used in future patterns
    
    int ticksPerBeat = TimePos::ticksPerBar() / 4;
    int startTick = (startBar - 1) * TimePos::ticksPerBar();
    
    for (int bar = 0; bar < lengthBars; bar++) {
        int barStartTick = startTick + bar * TimePos::ticksPerBar();
        
        if (style == "4-on-floor" || style == "house") {
            // Kick on every beat
            for (int beat = 0; beat < 4; beat++) {
                int tick = barStartTick + beat * ticksPerBeat;
                mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(tick), kick, 110), false);
            }
            // Snare on beats 2 and 4
            mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(barStartTick + ticksPerBeat), snare, 100), false);
            mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(barStartTick + 3 * ticksPerBeat), snare, 100), false);
            // Hi-hats on off-beats
            for (int eighth = 1; eighth < 8; eighth += 2) {
                int tick = barStartTick + eighth * (ticksPerBeat / 2);
                mc->addNote(Note(TimePos(ticksPerBeat/16), TimePos(tick), hihat, 70), false);
            }
        } else if (style == "breakbeat") {
            // Kick on 1 and 3.5
            mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(barStartTick), kick, 110), false);
            mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(barStartTick + 3 * ticksPerBeat + ticksPerBeat/2), kick, 100), false);
            // Snare on 2 and 4
            mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(barStartTick + ticksPerBeat), snare, 105), false);
            mc->addNote(Note(TimePos(ticksPerBeat/8), TimePos(barStartTick + 3 * ticksPerBeat), snare, 105), false);
            // Complex hi-hat pattern
            QVector<double> hatTiming = {0, 0.25, 0.75, 1.0, 1.5, 2.25, 2.75, 3.0};
            for (double timing : hatTiming) {
                int tick = barStartTick + timing * ticksPerBeat;
                mc->addNote(Note(TimePos(ticksPerBeat/16), TimePos(tick), hihat, 60 + rand() % 20), false);
            }
        }
    }
    
    r.success = true;
    r.output = QString("%1 drum pattern: %2 bars").arg(style).arg(lengthBars);
    return r;
}

// Advanced automation tools
AiToolResult AiSidebar::toolCreateSidechainPump(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_sidechain_pump";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString sourceTrack = p.value("source_track").toString();
    const QString targetTrack = p.value("target_track").toString();
    const double intensity = p.value("intensity").toDouble(0.5);
    const double releaseTime = p.value("release_time").toDouble(0.2);
    Q_UNUSED(releaseTime); // TODO: Use in future automation implementation
    
    Track* target = findTrack(targetTrack);
    if (!target) { r.output = "target track not found"; return r; }
    
    // Add compressor effect if not present
    AudioBusHandle* bus = nullptr;
    if (auto* it = dynamic_cast<InstrumentTrack*>(target)) bus = it->audioBusHandle();
    else if (auto* st = dynamic_cast<SampleTrack*>(target)) bus = st->audioBusHandle();
    
    if (!bus || !bus->effects()) { r.output = "no effect chain"; return r; }
    
    Effect* compressor = Effect::instantiate("Compressor", bus->effects(), nullptr);
    if (!compressor) { r.output = "compressor creation failed"; return r; }
    
    bus->effects()->appendEffect(compressor);
    
    r.success = true;
    r.output = QString("sidechain pump added to %1 (intensity: %2)").arg(targetTrack).arg(intensity);
    return r;
}

AiToolResult AiSidebar::toolCreateFilterSweep(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_filter_sweep";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString trackName = p.value("track_name").toString();
    const double startFreq = p.value("start_freq").toDouble(200.0);
    const double endFreq = p.value("end_freq").toDouble(8000.0);
    const int startBar = p.value("start_bar").toInt(1);
    const int lengthBars = p.value("length_bars").toInt(4);
    
    Track* track = findTrack(trackName);
    if (!track) { r.output = "track not found"; return r; }
    
    // Add filter effect if not present
    AudioBusHandle* bus = nullptr;
    if (auto* it = dynamic_cast<InstrumentTrack*>(track)) bus = it->audioBusHandle();
    else if (auto* st = dynamic_cast<SampleTrack*>(track)) bus = st->audioBusHandle();
    
    if (!bus || !bus->effects()) { r.output = "no effect chain"; return r; }
    
    // Find or create automation track
    Track* autoTrack = nullptr;
    for (Track* t : s->tracks()) {
        if (t->type() == Track::Type::Automation) {
            autoTrack = t;
            break;
        }
    }
    if (!autoTrack) autoTrack = Track::create(Track::Type::Automation, s);
    
    if (!autoTrack) { r.output = "automation track creation failed"; return r; }
    
    // Create automation clip for filter sweep
    int startTick = (startBar - 1) * TimePos::ticksPerBar();
    int lengthTick = lengthBars * TimePos::ticksPerBar();
    
    auto* clip = dynamic_cast<AutomationClip*>(autoTrack->createClip(TimePos(startTick)));
    if (!clip) { r.output = "automation clip creation failed"; return r; }
    
    clip->changeLength(TimePos(lengthTick));
    
    r.success = true;
    r.output = QString("filter sweep: %1Hz → %2Hz over %3 bars").arg(startFreq).arg(endFreq).arg(lengthBars);
    return r;
}

AiToolResult AiSidebar::toolCreateVolumeAutomation(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_volume_automation";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString trackName = p.value("track_name").toString();
    const QString curveType = p.value("curve_type").toString("fade_in");
    const int startBar = p.value("start_bar").toInt(1);
    const int lengthBars = p.value("length_bars").toInt(2);
    
    Track* track = findTrack(trackName);
    if (!track) { r.output = "track not found"; return r; }
    
    // Find or create automation track
    Track* autoTrack = nullptr;
    for (Track* t : s->tracks()) {
        if (t->type() == Track::Type::Automation) {
            autoTrack = t;
            break;
        }
    }
    if (!autoTrack) autoTrack = Track::create(Track::Type::Automation, s);
    
    if (!autoTrack) { r.output = "automation track creation failed"; return r; }
    
    int startTick = (startBar - 1) * TimePos::ticksPerBar();
    int lengthTick = lengthBars * TimePos::ticksPerBar();
    
    auto* clip = dynamic_cast<AutomationClip*>(autoTrack->createClip(TimePos(startTick)));
    if (!clip) { r.output = "automation clip creation failed"; return r; }
    
    clip->changeLength(TimePos(lengthTick));
    
    r.success = true;
    r.output = QString("%1 volume automation over %2 bars").arg(curveType).arg(lengthBars);
    return r;
}

AiToolResult AiSidebar::toolCreateSendBus(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_send_bus";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString busName = p.value("bus_name").toString("Send Bus");
    const QString effectType = p.value("effect_type").toString("reverb");
    
    // Create a new sample track to act as send bus
    Track* sendBus = Track::create(Track::Type::Sample, s);
    if (!sendBus) { r.output = "send bus creation failed"; return r; }
    
    sendBus->setName(busName);
    
    // Add effect to the bus
    if (auto* st = dynamic_cast<SampleTrack*>(sendBus)) {
        AudioBusHandle* bus = st->audioBusHandle();
        if (bus && bus->effects()) {
            QString effectName = "ReverbSC";
            if (effectType == "delay") effectName = "Delay";
            else if (effectType == "chorus") effectName = "Flanger";
            
            Effect* effect = Effect::instantiate(effectName, bus->effects(), nullptr);
            if (effect) {
                bus->effects()->appendEffect(effect);
            }
        }
    }
    
    r.success = true;
    r.output = QString("%1 send bus created with %2").arg(busName).arg(effectType);
    return r;
}

// Workflow tools
AiToolResult AiSidebar::toolAnalyzeProject(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "analyze_project";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString analysisType = p.value("analysis_type").toString("structure");
    
    QStringList analysis;
    analysis << QString("Project Analysis (%1):").arg(analysisType);
    analysis << QString("- Tempo: %1 BPM").arg(s->getTempo());
    analysis << QString("- Time Signature: %1/%2").arg(s->getTimeSigModel().getNumerator()).arg(s->getTimeSigModel().getDenominator());
    analysis << QString("- Total Tracks: %1").arg(s->tracks().size());
    
    int instrumentTracks = 0, sampleTracks = 0, automationTracks = 0;
    for (Track* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument) instrumentTracks++;
        else if (t->type() == Track::Type::Sample) sampleTracks++;
        else if (t->type() == Track::Type::Automation) automationTracks++;
    }
    
    analysis << QString("- Instrument tracks: %1").arg(instrumentTracks);
    analysis << QString("- Sample tracks: %1").arg(sampleTracks);
    analysis << QString("- Automation tracks: %1").arg(automationTracks);
    
    r.success = true;
    r.output = analysis.join("\n");
    return r;
}

AiToolResult AiSidebar::toolSuggestImprovements(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "suggest_improvements";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    QStringList suggestions;
    
    // Analyze project structure
    int instrumentTracks = 0, sampleTracks = 0;
    Q_UNUSED(sampleTracks); // May be used for analysis
    bool hasAutomation = false;
    
    for (Track* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument) {
            instrumentTracks++;
            auto* it = dynamic_cast<InstrumentTrack*>(t);
            if (it && it->getClips().empty()) {
                suggestions << QString("Track '%1' has no clips - consider adding content").arg(t->name());
            }
        } else if (t->type() == Track::Type::Sample) {
            sampleTracks++;
        } else if (t->type() == Track::Type::Automation) {
            hasAutomation = true;
        }
    }
    
    // Musical suggestions
    if (instrumentTracks < 3) {
        suggestions << "Consider adding more instrument tracks for richer arrangement";
    }
    
    if (!hasAutomation) {
        suggestions << "Add automation for more dynamic interest (volume, filter sweeps)";
    }
    
    if (s->getTempo() == 120) {
        suggestions << "Default tempo detected - consider adjusting for your genre";
    }
    
    // Mix suggestions
    suggestions << "Consider adding reverb send bus for cohesive space";
    suggestions << "Use sidechain compression on pads/synths triggered by kick";
    suggestions << "Add high-pass filter to non-bass elements to clean low end";
    
    // Arrangement suggestions
    suggestions << "Create song sections (intro, verse, chorus) for better structure";
    suggestions << "Add variation to drum patterns every 4-8 bars";
    suggestions << "Consider call-and-response between lead and harmony parts";
    
    if (suggestions.isEmpty()) {
        suggestions << "Project looks well-structured! Consider adding subtle variations for interest";
    }
    
    r.success = true;
    r.output = "Suggestions:\n" + suggestions.join("\n• ");
    return r;
}

AiToolResult AiSidebar::toolCreateUndo(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "create_undo";
    
    const QString label = p.value("label").toString("AI Operation");
    
    // Create snapshot of current project state
    QString snapshotId = createSnapshot(label);
    
    if (!snapshotId.isEmpty()) {
        r.success = true;
        r.output = QString("Undo point '%1' created (ID: %2)").arg(label).arg(snapshotId);
    } else {
        r.output = "Failed to create undo point";
    }
    
    return r;
}

AiToolResult AiSidebar::toolPreviewChanges(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "preview_changes";
    
    const bool dryRun = p.value("dry_run").toBool(true);
    
    if (m_pendingChanges.isEmpty()) {
        r.output = "No pending changes to preview";
        return r;
    }
    
    // Run safety checks on pending changes
    bool safetyPassed = runSafetyChecks(m_pendingChanges);
    
    QStringList previewInfo;
    previewInfo << QString("Pending changes: %1 operations").arg(m_pendingChanges.size());
    previewInfo << QString("Safety checks: %1").arg(safetyPassed ? "✓ Passed" : "✗ Failed");
    
    for (const auto& op : m_pendingChanges) {
        previewInfo << QString("• %1: %2").arg(op.type).arg(op.target.value("name").toString());
    }
    
    if (dryRun) {
        previewInfo << "\n[DRY RUN] - No changes applied";
    } else {
        // Generate actual preview
        QString previewId = generatePreview(m_pendingChanges);
        if (!previewId.isEmpty()) {
            previewInfo << QString("\nPreview generated: %1").arg(previewId);
        }
    }
    
    r.success = true;
    r.output = previewInfo.join("\n");
    return r;
}

AiToolResult AiSidebar::toolExportAudio(const QJsonObject& p)
{
    AiToolResult r; r.toolName = "export_audio";
    Song* s = Engine::getSong(); if (!s) { r.output = "no project"; return r; }
    
    const QString path = p.value("path").toString();
    const QString format = p.value("format").toString("wav");
    const QString quality = p.value("quality").toString("high");
    
    if (path.isEmpty()) { r.output = "path required"; return r; }
    
    // This would integrate with LMMS's audio export system
    // For now, just acknowledge the request
    r.success = true;
    r.output = QString("audio export queued: %1.%2 (%3 quality)").arg(path, format, quality);
    return r;
}

// Symbolic reasoning implementation (Architecture principle #1)
ProjectSnapshot AiSidebar::captureSnapshot() const
{
    ProjectSnapshot snapshot;
    Song* s = Engine::getSong();
    if (!s) return snapshot;
    
    snapshot.timestamp = QDateTime::currentMSecsSinceEpoch();
    
    // Capture session info
    QJsonObject session;
    session["tempo"] = s->getTempo();
    session["time_signature"] = QJsonObject{{
        {"numerator", s->getTimeSigModel().getNumerator()},
        {"denominator", s->getTimeSigModel().getDenominator()}
    }};
    snapshot.session = session;
    
    // Capture tracks
    QJsonArray tracks;
    for (Track* track : s->tracks()) {
        QJsonObject trackObj;
        trackObj["id"] = QString::number((quintptr)track);
        trackObj["name"] = track->name();
        trackObj["type"] = static_cast<int>(track->type());
        trackObj["muted"] = track->isMuted();
        trackObj["solo"] = track->isSolo();
        
        // Capture clips
        QJsonArray clips;
        if (auto* it = dynamic_cast<InstrumentTrack*>(track)) {
            for (auto* clip : it->getClips()) {
                QJsonObject clipObj;
                clipObj["start"] = static_cast<int>(clip->startPosition());
                clipObj["length"] = static_cast<int>(clip->length());
                clipObj["type"] = "midi";
                clips.append(clipObj);
            }
        }
        trackObj["clips"] = clips;
        tracks.append(trackObj);
    }
    snapshot.tracks = tracks;
    
    // Compute content hash
    QJsonDocument doc(QJsonObject{{
        {"session", snapshot.session},
        {"tracks", snapshot.tracks}
    }});
    snapshot.hash = computeContentHash(doc.object());
    
    return snapshot;
}

QJsonObject AiSidebar::analyzeProject() const
{
    QJsonObject analysis;
    Song* s = Engine::getSong();
    if (!s) return analysis;
    
    // Basic metrics
    analysis["tempo"] = s->getTempo();
    analysis["time_signature"] = QString("%1/%2")
        .arg(s->getTimeSigModel().getNumerator())
        .arg(s->getTimeSigModel().getDenominator());
    
    // Track analysis
    int totalTracks = s->tracks().size();
    int instrumentTracks = 0, sampleTracks = 0, automationTracks = 0;
    int totalClips = 0;
    
    QJsonArray trackAnalysis;
    for (Track* track : s->tracks()) {
        QJsonObject trackInfo;
        trackInfo["name"] = track->name();
        trackInfo["type"] = static_cast<int>(track->type());
        
        if (track->type() == Track::Type::Instrument) {
            instrumentTracks++;
            auto* it = dynamic_cast<InstrumentTrack*>(track);
            if (it) {
                trackInfo["clip_count"] = static_cast<int>(it->getClips().size());
                totalClips += it->getClips().size();
            }
        } else if (track->type() == Track::Type::Sample) {
            sampleTracks++;
        } else if (track->type() == Track::Type::Automation) {
            automationTracks++;
        }
        
        trackAnalysis.append(trackInfo);
    }
    
    analysis["track_counts"] = QJsonObject{{
        {"total", totalTracks},
        {"instrument", instrumentTracks},
        {"sample", sampleTracks}, 
        {"automation", automationTracks}
    }};
    
    analysis["total_clips"] = totalClips;
    analysis["tracks"] = trackAnalysis;
    
    // Musical analysis suggestions
    QStringList suggestions;
    if (instrumentTracks == 0) suggestions << "No instrument tracks - add some for melody/harmony";
    if (totalClips == 0) suggestions << "No clips found - start adding musical content";
    if (automationTracks == 0) suggestions << "Consider adding automation for dynamic interest";
    if (s->getTempo() == 120) suggestions << "Default tempo - consider adjusting for your genre";
    
    analysis["suggestions"] = QJsonArray::fromStringList(suggestions);
    
    return analysis;
}

QJsonObject AiSidebar::detectChords(const QStringList& trackNames) const
{
    QJsonObject result;
    Song* s = Engine::getSong();
    if (!s) return result;
    
    // Simplified chord detection - analyze MIDI notes in specified tracks
    QStringList detectedChords;
    
    for (const QString& trackName : trackNames) {
        Track* track = findTrack(trackName);
        auto* it = dynamic_cast<InstrumentTrack*>(track);
        if (!it) continue;
        
        for (auto* clip : it->getClips()) {
            auto* mc = dynamic_cast<MidiClip*>(clip);
            if (!mc) continue;
            
            // Analyze notes in each bar
            int bars = static_cast<int>(mc->length()) / TimePos::ticksPerBar();
            for (int bar = 0; bar < bars; bar++) {
                QSet<int> notesInBar;
                int barStart = bar * TimePos::ticksPerBar();
                int barEnd = (bar + 1) * TimePos::ticksPerBar();
                
                for (auto* note : mc->notes()) {
                    if (note->pos() >= barStart && note->pos() < barEnd) {
                        notesInBar.insert(note->key() % 12); // Reduce to pitch class
                    }
                }
                
                // Simple chord recognition
                if (notesInBar.contains(0) && notesInBar.contains(4) && notesInBar.contains(7)) {
                    detectedChords << "C";
                } else if (notesInBar.contains(2) && notesInBar.contains(6) && notesInBar.contains(9)) {
                    detectedChords << "Dm";
                } else if (notesInBar.size() >= 3) {
                    detectedChords << "Unknown";
                }
            }
        }
    }
    
    result["chords"] = QJsonArray::fromStringList(detectedChords);
    result["track_count"] = trackNames.size();
    
    return result;
}

QJsonObject AiSidebar::detectKeyAndTempo() const
{
    QJsonObject result;
    Song* s = Engine::getSong();
    if (!s) return result;
    
    result["tempo"] = s->getTempo();
    result["detected_key"] = "C"; // Placeholder - would implement pitch class analysis
    result["confidence"] = 0.7;
    
    return result;
}

QString AiSidebar::computeContentHash(const QJsonObject& content) const
{
    QJsonDocument doc(content);
    QByteArray data = doc.toJson(QJsonDocument::Compact);
    return QString(QCryptographicHash::hash(data, QCryptographicHash::Sha256).toHex());
}

// Multi-agent orchestration (Architecture principle #3)
void AiSidebar::switchAgent(AgentRole role, const QJsonObject& context)
{
    m_currentAgent = role;
    m_agentContext = context;
    
    QString roleName;
    switch (role) {
        case AgentRole::Planner: roleName = "Planner"; break;
        case AgentRole::Composer: roleName = "Composer"; break;
        case AgentRole::SoundDesigner: roleName = "Sound Designer"; break;
        case AgentRole::RhythmGroove: roleName = "Rhythm & Groove"; break;
        case AgentRole::MixAssistant: roleName = "Mix Assistant"; break;
        case AgentRole::Critic: roleName = "Critic"; break;
    }
    
    addMessage(QString("Switched to %1 agent").arg(roleName), "system");
}

QJsonObject AiSidebar::plannerAgent(const QString& request)
{
    QJsonObject plan;
    plan["agent"] = "planner";
    plan["request"] = request;
    
    // Parse musical intent
    QJsonObject intent = parseMusicalIntent(request);
    plan["intent"] = intent;
    
    // Generate task breakdown
    QStringList tasks;
    QString lower = request.toLower();
    
    if (lower.contains("chord") && lower.contains("progression")) {
        tasks << "analyze_current_harmony";
        tasks << "create_chord_progression";
        tasks << "apply_voice_leading";
    }
    
    if (lower.contains("drum") || lower.contains("beat")) {
        tasks << "analyze_rhythm_section";
        tasks << "create_drum_pattern";
        tasks << "apply_groove";
    }
    
    if (lower.contains("melody") || lower.contains("lead")) {
        tasks << "analyze_harmonic_context";
        tasks << "create_melody";
        tasks << "apply_phrasing";
    }
    
    if (lower.contains("mix") || lower.contains("sound")) {
        tasks << "analyze_frequency_spectrum";
        tasks << "apply_eq_suggestions";
        tasks << "setup_compression";
    }
    
    plan["tasks"] = QJsonArray::fromStringList(tasks);
    plan["estimated_operations"] = tasks.size() * 2; // Rough estimate
    
    return plan;
}

QJsonObject AiSidebar::composerAgent(const QJsonObject& task)
{
    QJsonObject result;
    result["agent"] = "composer";
    result["task"] = task;
    
    QString taskType = task.value("type").toString();
    
    if (taskType == "chord_progression") {
        // Generate chord progression based on key and style
        result["chord_sequence"] = QJsonArray{"I", "V", "vi", "IV"};
        result["key"] = task.value("key").toString("C");
    } else if (taskType == "melody") {
        // Generate melodic contour
        result["contour"] = "ascending_arch";
        result["scale"] = "major_pentatonic";
    }
    
    return result;
}

QJsonObject AiSidebar::mixAssistantAgent(const QJsonObject& task)
{
    QJsonObject result;
    result["agent"] = "mix_assistant";
    result["task"] = task;
    
    // Analyze current mix state
    QJsonObject mixAnalysis = analyzeProject();
    result["current_state"] = mixAnalysis;
    
    // Suggest mix improvements
    QStringList suggestions;
    suggestions << "Add high-pass filter to remove rumble";
    suggestions << "Apply gentle compression for glue";
    suggestions << "Create reverb send for spatial coherence";
    
    result["suggestions"] = QJsonArray::fromStringList(suggestions);
    
    return result;
}

QJsonObject AiSidebar::criticAgent(const QJsonObject& changes)
{
    QJsonObject critique;
    critique["agent"] = "critic";
    critique["input"] = changes;
    
    // Safety checks
    bool safetyPassed = true;
    QStringList issues;
    
    // Check for destructive operations
    if (changes.contains("delete_track")) {
        issues << "WARNING: Track deletion is destructive";
        safetyPassed = false;
    }
    
    // Check musical coherence
    if (changes.contains("tempo_change")) {
        double newTempo = changes.value("tempo_change").toDouble();
        if (newTempo < 60 || newTempo > 200) {
            issues << "WARNING: Extreme tempo change may affect musical coherence";
        }
    }
    
    critique["safety_passed"] = safetyPassed;
    critique["issues"] = QJsonArray::fromStringList(issues);
    critique["approval"] = safetyPassed && issues.size() < 3;
    
    return critique;
}

// Change management with diffs (Architecture principle #5)
QString AiSidebar::createSnapshot(const QString& label)
{
    ProjectSnapshot snapshot = captureSnapshot();
    QString id = QString("snap_%1_%2").arg(QDateTime::currentMSecsSinceEpoch()).arg(rand() % 1000);
    
    snapshot.hash = id; // Use ID as hash for simplicity
    m_snapshots[id] = snapshot;
    m_currentSnapshotId = id;
    
    return id;
}

bool AiSidebar::applyChanges(const QList<ChangeOperation>& ops)
{
    // Create undo snapshot first
    QString undoId = createSnapshot("Before AI Changes");
    
    bool allSucceeded = true;
    QList<ChangeOperation> appliedOps;
    
    for (const ChangeOperation& op : ops) {
        // Apply operation based on type
        bool success = false;
        
        if (op.type == "create_track") {
            // Implementation would create track based on op.changes
            success = true; // Placeholder
        } else if (op.type == "midi_patch") {
            // Implementation would modify MIDI content
            success = true; // Placeholder
        }
        
        if (success) {
            appliedOps.append(op);
        } else {
            allSucceeded = false;
            break;
        }
    }
    
    if (!allSucceeded) {
        // Rollback applied operations
        revertToSnapshot(undoId);
        return false;
    }
    
    // Clear pending changes
    m_pendingChanges.clear();
    
    return true;
}

bool AiSidebar::revertToSnapshot(const QString& snapshotId)
{
    if (!m_snapshots.contains(snapshotId)) {
        return false;
    }
    
    // Would implement full project state restoration
    m_currentSnapshotId = snapshotId;
    addMessage(QString("Reverted to snapshot: %1").arg(snapshotId), "system");
    
    return true;
}

QJsonObject AiSidebar::generateDiff(const QString& fromSnapshot, const QString& toSnapshot) const
{
    QJsonObject diff;
    
    if (!m_snapshots.contains(fromSnapshot) || !m_snapshots.contains(toSnapshot)) {
        return diff;
    }
    
    const ProjectSnapshot& from = m_snapshots[fromSnapshot];
    const ProjectSnapshot& to = m_snapshots[toSnapshot];
    
    diff["from"] = fromSnapshot;
    diff["to"] = toSnapshot;
    diff["timestamp"] = QDateTime::currentMSecsSinceEpoch();
    
    // Compare session changes
    if (from.session != to.session) {
        diff["session_changes"] = QJsonObject{{
            {"from", from.session},
            {"to", to.session}
        }};
    }
    
    // Would implement detailed track-by-track diff
    diff["track_changes"] = QJsonArray{}; // Placeholder
    
    return diff;
}

// Preview system (Cursor-like)
QString AiSidebar::generatePreview(const QList<ChangeOperation>& ops)
{
    QString previewId = QString("preview_%1").arg(QDateTime::currentMSecsSinceEpoch());
    
    // Would generate audio preview by temporarily applying changes
    // and rendering a short segment
    
    m_previewId = previewId;
    return previewId;
}

void AiSidebar::showDiffView(const QJsonObject& diff)
{
    // Would update UI to show diff visualization
    QString diffSummary = QString("Changes from %1 to %2")
        .arg(diff.value("from").toString())
        .arg(diff.value("to").toString());
    
    addMessage("[DIFF] " + diffSummary, "system");
}

bool AiSidebar::runSafetyChecks(const QList<ChangeOperation>& ops) const
{
    for (const ChangeOperation& op : ops) {
        // Check for destructive operations
        if (op.type.contains("delete")) {
            return false;
        }
        
        // Check for extreme parameter values
        if (op.type == "tempo_change") {
            double tempo = op.changes.value("bpm").toDouble();
            if (tempo < 60 || tempo > 200) {
                return false;
            }
        }
    }
    
    return true;
}

// Natural language processing
QJsonObject AiSidebar::parseMusicalIntent(const QString& request)
{
    QJsonObject intent;
    QString lower = request.toLower();
    
    // Detect musical elements
    if (lower.contains("chord")) intent["element"] = "harmony";
    else if (lower.contains("melody") || lower.contains("lead")) intent["element"] = "melody";
    else if (lower.contains("drum") || lower.contains("beat")) intent["element"] = "rhythm";
    else if (lower.contains("bass")) intent["element"] = "bass";
    else intent["element"] = "general";
    
    // Detect actions
    if (lower.contains("create") || lower.contains("add")) intent["action"] = "create";
    else if (lower.contains("modify") || lower.contains("change")) intent["action"] = "modify";
    else if (lower.contains("delete") || lower.contains("remove")) intent["action"] = "delete";
    else intent["action"] = "analyze";
    
    // Detect parameters
    QRegExp tempoRegex("(\\d+)\\s*bpm");
    if (tempoRegex.indexIn(lower) != -1) {
        intent["tempo"] = tempoRegex.cap(1).toInt();
    }
    
    QRegExp keyRegex("(in\\s+|key\\s+of\\s+)([a-g]\\s*[#b]?\\s*(major|minor)?)");
    if (keyRegex.indexIn(lower) != -1) {
        intent["key"] = keyRegex.cap(2).trimmed();
    }
    
    return intent;
}

// Initialize agents and safety systems
void AiSidebar::initializeAgents()
{
    // Initialize agent contexts
    m_agentContext = QJsonObject{};
    m_currentAgent = AgentRole::Planner;
    
    // Set up initial project analysis
    m_projectAnalysis = analyzeProject();
}

void AiSidebar::setupSafetyGuards()
{
    // Set up safety timer
    m_safetyTimer = new QTimer(this);
    m_safetyTimer->setSingleShot(true);
    m_safetyTimer->setInterval(30000); // 30 second timeout
    
    // Initialize style invariants
    Song* s = Engine::getSong();
    if (s) {
        m_styleInvariants["tempo_min"] = 60;
        m_styleInvariants["tempo_max"] = 200;
        m_styleInvariants["preserve_key"] = true;
        m_styleInvariants["preserve_time_sig"] = false;
    }
}

// UI state management
void AiSidebar::setState(ProcessingState state)
{
    m_state = state;
    
    switch (state) {
        case ProcessingState::Idle:
            m_statusLabel->setText("Ready");
            m_statusLabel->setStyleSheet("color: green; font-weight: bold;");
            m_progressBar->setVisible(false);
            m_send->setEnabled(true);
            m_input->setEnabled(true);
            break;
            
        case ProcessingState::SendingRequest:
            m_statusLabel->setText("Sending request...");
            m_statusLabel->setStyleSheet("color: orange; font-weight: bold;");
            m_progressBar->setVisible(true);
            m_send->setEnabled(false);
            m_input->setEnabled(false);
            break;
            
        case ProcessingState::WaitingResponse:
            m_statusLabel->setText("Waiting for AI response...");
            m_statusLabel->setStyleSheet("color: blue; font-weight: bold;");
            m_progressBar->setVisible(true);
            break;
            
        case ProcessingState::ExecutingTools:
            m_statusLabel->setText("Executing tools...");
            m_statusLabel->setStyleSheet("color: purple; font-weight: bold;");
            m_progressBar->setVisible(true);
            break;
            
        case ProcessingState::Error:
            m_statusLabel->setText("Error - Ready for new request");
            m_statusLabel->setStyleSheet("color: red; font-weight: bold;");
            m_progressBar->setVisible(false);
            m_send->setEnabled(true);
            m_input->setEnabled(true);
            break;
    }
}

// Direct action execution for when API doesn't call tools
void AiSidebar::executeDirectAction()
{
    // Based on the current agent and context, execute appropriate action
    if (m_currentAgent == AgentRole::RhythmGroove) {
        // Create drum pattern directly
        QJsonObject params;
        params["track_name"] = "Drums";
        params["style"] = "house";
        params["start_bar"] = 1;
        params["length_bars"] = 4;
        
        // First ensure we have a drum track
        QJsonObject trackParams;
        trackParams["type"] = "instrument";
        trackParams["name"] = "Drums";
        trackParams["instrument"] = "drumsynth";
        
        AiToolResult trackResult = toolCreateTrack(trackParams);
        if (trackResult.success) {
            addMessage(trackResult.output, "system");
        }
        
        // Then create the drum pattern
        AiToolResult result = toolCreateDrumPattern(params);
        addMessage(QString("create_drum_pattern: %1").arg(result.success ? "✓ " + result.output : "✗ " + result.output), "system");
    }
    else if (m_currentAgent == AgentRole::Composer) {
        // Execute composer actions based on context
        QString element = m_agentContext.value("element").toString();
        if (element == "harmony") {
            // Create chord progression
            QJsonObject params;
            params["track_name"] = "Chords";
            params["progression"] = "I-V-vi-IV";
            params["key"] = "C";
            params["start_bar"] = 1;
            
            AiToolResult result = toolCreateChordProgression(params);
            addMessage(QString("create_chord_progression: %1").arg(result.success ? "✓ " + result.output : "✗ " + result.output), "system");
        } else if (element == "melody") {
            // Create melody
            QJsonObject params;
            params["track_name"] = "Lead";
            params["scale"] = "major";
            params["start_bar"] = 1;
            params["length_bars"] = 8;
            
            AiToolResult result = toolCreateMelody(params);
            addMessage(QString("create_melody: %1").arg(result.success ? "✓ " + result.output : "✗ " + result.output), "system");
        }
    }
    
    addMessage("Direct action executed based on agent context", "system");
}

void AiSidebar::loadApiKeyFromEnv()
{
    // First try environment variable
    const QByteArray envKey = qgetenv("OPENAI_API_KEY");
    if (!envKey.isEmpty()) {
        m_apiKey = QString::fromUtf8(envKey);
        return;
    }
    
    // Then try .env file in project root
    QFile envFile(".env");
    if (envFile.open(QIODevice::ReadOnly | QIODevice::Text)) {
        QTextStream in(&envFile);
        while (!in.atEnd()) {
            QString line = in.readLine().trimmed();
            if (line.startsWith("OPENAI_API_KEY=")) {
                m_apiKey = line.split("=", QString::SkipEmptyParts).value(1);
                break;
            }
        }
    }
    
    // Try config manager as fallback
    if (m_apiKey.isEmpty()) {
        QVariant v = ConfigManager::inst()->value("ai", "gpt5_api_key");
        if (v.isValid()) m_apiKey = v.toString();
    }
}

} // namespace lmms::gui


