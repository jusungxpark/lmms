// (moved function bodies appear later within the namespace)
/*
 * AssistantPanel.cpp - NL assistant panel for LMMS
 */

#include "AssistantPanel.h"
#include "AssistantActions.h"
#include "AssistantCommandBus.h"

#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QListWidget>
#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <algorithm>
#include <QEvent>
#include <QKeyEvent>
#include <QRegularExpression>
#include <QCheckBox>

#include "Engine.h"
#include "Song.h"
#include "TrackContainer.h"
#include "Track.h"
#include "InstrumentTrack.h"
#include "MidiClip.h"
#include "Note.h"
#include "Plugin.h"
#include "Effect.h"
#include "EffectChain.h"
#include "EffectSelectDialog.h"
#include "TimePos.h"
#include "volume.h"
#include "Clip.h"
#include "embed.h"
#include "ModelClient.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

using namespace lmms;

namespace lmms::gui {

bool AssistantPanel::tryMakeBeat(const QString& text)
{
    if (!text.contains(QRegularExpression("(?i)^(make|create).*(beat|loop|groove)"))) return false;
    auto* kick = getOrCreateInstrument("Kick", "kicker");
    auto* hats = getOrCreateInstrument("Hats", "tripleoscillator");
    auto* bass = getOrCreateInstrument("Bass", "tripleoscillator");
    if (!kick || !hats || !bass) return false;
    const int bar = TimePos::ticksPerBar();
    const int beat = bar / 4;
    for (int i = 0; i < 16; ++i) addNote(kick, i * beat, beat/2, 36);
    for (int i = 0; i < 16; ++i) addNote(hats, i * beat + beat/2, beat/4, 72);
    for (int i = 0; i < 8; ++i) addNote(bass, i * (beat*2), beat, 48);
    Engine::getSong()->setModified();
    log(tr("Beat created (4 bars)"));
    return true;
}

bool AssistantPanel::tryHelp(const QString& text)
{
    if (!text.contains(QRegularExpression("(?i)^(what can you do|help|capabilities|commands)$"))) return false;
    log(tr("You can ask: make a beat, set tempo, add instrument/effect, quantize, transpose, loop, style (aggressive/jazzy), or 'create sample edm track'."));
    return true;
}

bool AssistantPanel::tryRemoveTrack(const QString& text)
{
    static const QRegularExpression re("(?i)^(remove|delete)\\s+the\\s+(?<name>[A-Za-z0-9_ -]+)$");
    auto m = re.match(text.trimmed());
    if (!m.hasMatch()) return false;
    const auto name = m.captured("name").trimmed();
    if (removeInstrumentTrackByName(name)) { log(tr("Removed track '%1'").arg(name)); return true; }
    log(tr("Track '%1' not found").arg(name));
    return true; // handled intent
}

bool AssistantPanel::removeInstrumentTrackByName(const QString& name)
{
    auto song = Engine::getSong();
    if (!song) return false;
    for (auto* t : song->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(name, Qt::CaseInsensitive) == 0) {
            song->removeTrack(t);
            song->setModified();
            return true;
        }
    }
    return false;
}

bool AssistantPanel::tryIntensifyKicker(const QString& text)
{
    if (!text.contains(QRegularExpression("(?i)(make|turn).*kicker.*(more intense|harder|punchy)"))) return false;
    auto* it = findInstrumentTrackByName("Kick");
    if (!it) it = findInstrumentTrackByName("Kicker");
    if (!it) return false;
    // Try to access Kicker parameters via Instrument API if available
    if (auto* inst = it->instrument()) {
        // Best-effort: adjust gain if exposed
        if (auto* vol = it->volumeModel()) {
            vol->setValue(std::min(vol->maxValue(), vol->value() + 3.0f));
        }
    }
    addEffectToInstrumentTrack(it, "compressor");
    log(tr("Intensified Kicker (gain + compressor)"));
    Engine::getSong()->setModified();
    return true;
}

lmms::InstrumentTrack* AssistantPanel::getOrCreateInstrument(const QString& name, const QString& pluginFallback)
{
    if (auto* it = findInstrumentTrackByName(name)) return it;
    return addInstrumentTrack(pluginFallback, name);
}

void AssistantPanel::addNote(lmms::InstrumentTrack* it, int start, int len, int key)
{
    if (!it) return;
    auto* mc = ensureMidiClip(it, 0, TimePos::ticksPerBar()*4);
    Note n(TimePos(len), TimePos(start), key);
    mc->addNote(n, false);
    mc->rearrangeAllNotes();
}
AssistantPanel::AssistantPanel(QWidget* parent)
    : SideBarWidget(tr("Assistant"), embed::getIconPixmap("help"), parent)
    , m_actions(new AssistantActions())
{
    auto root = new QWidget(this);
    auto layout = new QVBoxLayout(root);
    layout->setContentsMargins(8, 8, 8, 8);
    layout->setSpacing(6);

    m_logList = new QListWidget(root);
    m_logList->setObjectName("assistantLog");
    m_logList->setMinimumHeight(120);
    layout->addWidget(m_logList);

    auto row = new QWidget(root);
    auto rowLayout = new QHBoxLayout(row);
    rowLayout->setContentsMargins(0,0,0,0);
    m_input = new QLineEdit(row);
    m_input->setPlaceholderText(tr("e.g. Transpose Bass -2; set tempo 128; add effect Saturation on Lead"));
    m_runBtn = new QPushButton(tr("Run"), row);
    m_aiToggle = new QCheckBox(tr("Use GPT-5"), row);
    m_aiToggle->setChecked(true);
    rowLayout->addWidget(m_input);
    rowLayout->addWidget(m_runBtn);
    rowLayout->addWidget(m_aiToggle);
    layout->addWidget(row);

    addContentWidget(root);

    connect(m_runBtn, &QPushButton::clicked, this, &AssistantPanel::onSubmit);
    connect(m_input, &QLineEdit::returnPressed, this, &AssistantPanel::onSubmit);

    // UX: focus input, select all; install history key handling
    m_input->installEventFilter(this);
    m_input->setFocus(Qt::OtherFocusReason);

    // Future: hook a model client; for now we just construct it without network
    // and leave the API key unset (settable later via settings).
    m_modelClient = new ModelClient(this);
    // Optional: read API key from env to avoid storing secrets in code.
    if (const QByteArray envKey = qgetenv("OPENAI_API_KEY"); !envKey.isEmpty()) {
        m_modelClient->setApiKey(QString::fromUtf8(envKey));
        m_modelClient->setModel(QStringLiteral("gpt-5"));
        m_modelClient->setTemperature(0.4);
    }

    // Hook model plan output: when a JSON plan arrives, execute steps
    connect(m_modelClient, &ModelClient::planReady, this, &AssistantPanel::handleModelPlan);
    connect(m_modelClient, &ModelClient::errorOccurred, this, [this](const QString& msg){
        m_logList->addItem(tr("Model error: %1").arg(msg));
        m_logList->scrollToBottom();
    });
    connect(m_modelClient, &ModelClient::requestStarted, this, [this]() {
        m_logList->addItem(tr("Thinking with GPT-5…"));
        m_logList->scrollToBottom();
    });
    // Reduce log spam: show only when total increases or every ~512 bytes
    connect(m_modelClient, &ModelClient::requestProgress, this, [this](qint64 rec, qint64 tot){
        static qint64 lastShown = 0;
        if (rec - lastShown < 512 && rec != tot) return;
        lastShown = rec;
        if (tot > 0) log(tr("Received %1/%2 bytes").arg(rec).arg(tot));
        else log(tr("Received %1 bytes").arg(rec));
    });
    connect(m_modelClient, &ModelClient::requestFinished, this, [this]() {
        m_logList->addItem(tr("Model response finished"));
        m_logList->scrollToBottom();
    });
}

void AssistantPanel::onSubmit()
{
    const auto text = m_input->text().trimmed();
    if (text.isEmpty()) { return; }
    
    // ALWAYS use GPT-5 when AI is enabled (like Cursor)
    if (m_aiToggle && m_aiToggle->isChecked() && m_modelClient) {
        // Send EVERYTHING to GPT-5, let it figure out what to do
        const auto prompt = buildPlannerPrompt(text);
        m_modelClient->complete(prompt);
        log(tr("🤔 Thinking..."));
    } else {
        // Fallback to local command parsing only if AI is disabled
        executeCommand(text);
    }
    
    // UX: add to history, clear prompt, re-focus like Cursor
    if (m_history.isEmpty() || m_history.back() != text) { m_history.push_back(text); }
    m_historyPos = m_history.size();
    m_input->clear();
    m_input->setFocus(Qt::OtherFocusReason);
}

void AssistantPanel::executeCommand(const QString& text)
{
    // Try specific parsers in order. If any succeeds, log and return.
    if (trySetTempo(text)) { log(tr("Set tempo: %1").arg(text)); return; }
    if (tryTransposeTrack(text)) { log(tr("Transposed: %1").arg(text)); return; }
    if (tryAddEffect(text)) { log(tr("Added effect: %1").arg(text)); return; }
    if (tryQuantize(text)) { log(tr("Quantized: %1").arg(text)); return; }
    if (tryStyle(text)) { log(tr("Applied style: %1").arg(text)); return; }
    if (tryLoopRepeat(text) || tryLoopTimes(text)) { log(tr("Looped/repeated: %1").arg(text)); return; }
    if (tryMakeBeat(text)) { log(tr("Generated beat")); return; }
    if (tryRemoveTrack(text)) { return; }
    if (tryIntensifyKicker(text)) { return; }
    if (tryHelp(text)) { return; }
    if (tryCreateSampleEdm(text)) { log(tr("Created sample EDM setup: %1").arg(text)); return; }

    log(tr("Did not understand: %1").arg(text));
}

bool AssistantPanel::maybeInvokeModel(const QString& text)
{
    // This method is now deprecated - we ALWAYS use AI when enabled
    // Keeping for backward compatibility
    if (!m_aiToggle || !m_aiToggle->isChecked()) return false;
    if (!m_modelClient) return false;
    const auto prompt = buildPlannerPrompt(text);
    m_modelClient->complete(prompt);
    return true;
}

QString AssistantPanel::buildPlannerPrompt(const QString& userText) const
{
    // Comprehensive prompt like Cursor - tell GPT-5 everything it can do
    QString tools = R"(You are an AI music production assistant integrated directly into LMMS DAW, similar to how Cursor works in VSCode.
The user will give you natural language commands about making music. You understand music theory, production techniques, and can control all aspects of LMMS.

You must respond with a JSON object: {"plan": {"steps": [ ... ]}}
Each step is an object with an "action" and arguments. Supported actions:
- set_tempo {"bpm": number}
- add_instrument {"plugin": string, "name": string}
- add_effect {"track": string, "fx": string}
- add_midi_notes {"track": string, "notes": [{"start": ticks, "len": ticks, "key": midi}]}
- transpose {"track": string, "semitones": number}
- quantize {"grid": "1/2|1/4|1/8|1/16|1/32"}
- loop {"span": "4bars|1m|30s"}
Keep steps small and deterministic. No prose, JSON only.)";
    return tools + "\nUser goal: " + userText + "\nContext: Song is empty or minimal; prefer creating a playable 4-8 bar loop with kick, hats, bass, and optionally lead. Use 'Kick', 'Hats', 'Bass' track names.";
}

void AssistantPanel::handleModelPlan(const QString& responseJson)
{
    // Parse the JSON response from GPT
    QJsonParseError err{};
    const auto doc = QJsonDocument::fromJson(responseJson.toUtf8(), &err);
    if (err.error != QJsonParseError::NoError) {
        m_logList->addItem(tr("Model parse error: %1").arg(err.errorString()));
        m_logList->scrollToBottom();
        return;
    }
    
    // Parse the new format: {"intent": "...", "actions": [...]}
    QJsonObject root = doc.object();
    QString intent = root.value("intent").toString();
    QJsonArray actions = root.value("actions").toArray();
    
    // Fallback to old format if needed
    if (actions.isEmpty()) {
        QJsonObject plan = root.value("plan").toObject();
        actions = plan.value("steps").toArray();
    }
    
    if (actions.isEmpty()) {
        log(tr("Model responded with no actions. Using local fallback."));
        actions = buildFallbackPlan(QString());
    }
    
    // Log the intent if present
    if (!intent.isEmpty()) {
        log(tr("🎯 Intent: %1").arg(intent));
    }
    
    // Execute actions using the new AssistantActions system
    log(tr("📋 Executing %1 actions...").arg(actions.size()));
    
    for (const QJsonValue& val : actions) {
        QJsonObject actionObj = val.toObject();
        QString action = actionObj.value("action").toString();
        QJsonObject params = actionObj.value("params").toObject();
        
        // Execute through the new action system
        auto result = m_actions->execute(action, params);
        
        if (result.success) {
            log(tr("✅ %1").arg(result.message));
        } else {
            log(tr("❌ %1").arg(result.message));
        }
    }
    
    Engine::getSong()->setModified();
    log(tr("✅ Plan complete!"));
}

void AssistantPanel::log(const QString& message)
{
    m_logList->addItem(message);
    m_logList->scrollToBottom();
}

bool AssistantPanel::executeSteps(const QJsonArray& steps)
{
    int i = 0;
    for (const auto& v : steps) {
        const auto o = v.toObject();
        const auto action = o.value("action").toString();
        log(tr("Step %1: %2").arg(++i).arg(action));
        if (action == "set_tempo") {
            const int bpm = o.value("bpm").toInt();
            if (bpm > 0) { Engine::getSong()->tempoModel().setValue(bpm); log(tr("  -> tempo %1").arg(bpm)); }
        } else if (action == "add_instrument") {
            const auto plugin = o.value("plugin").toString();
            const auto name = o.value("name").toString(plugin);
            m_lastCreatedTrack = addInstrumentTrack(plugin, name);
            log(tr("  -> instrument '%1' using '%2'").arg(name, plugin));
        } else if (action == "add_effect") {
            const auto track = o.value("track").toString();
            const auto fx = o.value("fx").toString();
            if (auto* it = findInstrumentTrackByName(track)) { addEffectToInstrumentTrack(it, fx); log(tr("  -> effect '%1' on '%2'").arg(fx, track)); }
        } else if (action == "transpose") {
            const auto track = o.value("track").toString();
            const int semitones = o.value("semitones").toInt();
            InstrumentTrack* it = track.isEmpty() ? defaultInstrumentTrack() : findInstrumentTrackByName(track);
            if (it) { transposeInstrumentTrack(it, semitones); log(tr("  -> transpose '%1' by %2").arg(track).arg(semitones)); }
        } else if (action == "quantize") {
            const auto grid = o.value("grid").toString("1/16");
            tryQuantize(QStringLiteral("quantize %1").arg(grid));
            log(tr("  -> quantize %1").arg(grid));
        } else if (action == "loop") {
            const auto span = o.value("span").toString("4bars");
            tryLoopRepeat(QStringLiteral("loop %1 across song").arg(span));
            log(tr("  -> loop %1").arg(span));
        } else if (action == "add_midi_notes") {
            const auto trackName = o.value("track").toString().trimmed();
            InstrumentTrack* it = nullptr;
            if (!trackName.isEmpty()) {
                it = findInstrumentTrackByName(trackName);
                if (!it && m_lastCreatedTrack) {
                    it = m_lastCreatedTrack; // fallback to most recent
                    log(tr("  -> fallback to last created track '%1'").arg(it->name()));
                }
            } else {
                it = m_lastCreatedTrack ? m_lastCreatedTrack : defaultInstrumentTrack();
            }
            if (!it) { log(tr("  !! track not found")); continue; }
            auto* mc = ensureMidiClip(it, 0, TimePos::ticksPerBar()*4);
            for (const auto& nv : o.value("notes").toArray()) {
                auto no = nv.toObject();
                Note n(TimePos(no.value("len").toInt()), TimePos(no.value("start").toInt()), no.value("key").toInt());
                mc->addNote(n, false);
            }
            mc->rearrangeAllNotes();
            log(tr("  -> added %1 notes to %2").arg(o.value("notes").toArray().size()).arg(trackName));
        }
    }
    return true;
}

QJsonArray AssistantPanel::buildFallbackPlan(const QString&) const
{
    // Simple 128 BPM EDM seed with notes for 4 bars
    const int bar = TimePos::ticksPerBar();
    const int beat = bar / 4;

    // Kick: 4-on-the-floor across 4 bars
    QJsonArray notesKick;
    for (int i = 0; i < 16; ++i) {
        notesKick.append(QJsonObject{{"start", i * beat}, {"len", beat/2}, {"key", 36}});
    }

    // Hats: off-beat 8ths across 4 bars
    QJsonArray notesHats;
    for (int i = 0; i < 16; ++i) {
        notesHats.append(QJsonObject{{"start", i * beat + beat/2}, {"len", beat/4}, {"key", 72}});
    }

    // Bass: simple 1/2-beat pulses on root
    QJsonArray notesBass;
    for (int i = 0; i < 8; ++i) {
        notesBass.append(QJsonObject{{"start", i * (beat*2)}, {"len", beat}, {"key", 48}});
    }

    QJsonArray steps;
    steps.append(QJsonObject{{"action","set_tempo"},{"bpm",128}});
    steps.append(QJsonObject{{"action","add_instrument"},{"plugin","kicker"},{"name","Kick"}});
    steps.append(QJsonObject{{"action","add_midi_notes"},{"track","Kick"},{"notes",notesKick}});
    steps.append(QJsonObject{{"action","add_instrument"},{"plugin","tripleoscillator"},{"name","Hats"}});
    steps.append(QJsonObject{{"action","add_midi_notes"},{"track","Hats"},{"notes",notesHats}});
    steps.append(QJsonObject{{"action","add_instrument"},{"plugin","tripleoscillator"},{"name","Bass"}});
    steps.append(QJsonObject{{"action","add_midi_notes"},{"track","Bass"},{"notes",notesBass}});
    // Optional: loop the first clip to extend arrangement
    steps.append(QJsonObject{{"action","loop"},{"span","16bars"}});
    return steps;
}

bool AssistantPanel::eventFilter(QObject* obj, QEvent* event)
{
    if (obj == m_input && event->type() == QEvent::KeyPress)
    {
        auto* ke = static_cast<QKeyEvent*>(event);
        if (ke->key() == Qt::Key_Up)
        {
            if (!m_history.isEmpty())
            {
                m_historyPos = std::max(0, m_historyPos - 1);
                m_input->setText(m_history.at(m_historyPos));
                m_input->selectAll();
            }
            return true;
        }
        if (ke->key() == Qt::Key_Down)
        {
            if (!m_history.isEmpty())
            {
                m_historyPos = std::min(m_history.size(), m_historyPos + 1);
                if (m_historyPos >= m_history.size())
                {
                    m_input->clear();
                }
                else
                {
                    m_input->setText(m_history.at(m_historyPos));
                    m_input->selectAll();
                }
            }
            return true;
        }
        if (ke->key() == Qt::Key_Escape)
        {
            m_input->clear();
            return true;
        }
    }
    return SideBarWidget::eventFilter(obj, event);
}

bool AssistantPanel::tryQuantize(const QString& text)
{
    // Examples: "quantize Lead to 1/16", "quantize 1/8"
    static const QRegularExpression re1("(?i)\\bquantize\\s+(?<name>[A-Za-z0-9_ -]+)?\\s*(to\\s*)?(?<grid>1/2|1/4|1/8|1/16|1/32)");
    auto m = re1.match(text);
    if (!m.hasMatch()) { return false; }
    const auto gridStr = m.captured("grid");
    int ticks = parseGridToTicks(gridStr);
    if (ticks <= 0) { return false; }

    InstrumentTrack* it = nullptr;
    const auto name = m.captured("name").trimmed();
    if (!name.isEmpty()) { it = findInstrumentTrackByName(name); }
    if (!it) { it = defaultInstrumentTrack(); }
    if (!it) { return false; }

    it->addJournalCheckPoint();
    for (auto* clip : it->getClips()) {
        auto* mc = dynamic_cast<MidiClip*>(clip);
        if (!mc) { continue; }
        const auto& notes = mc->notes();
        for (auto* note : notes) {
            note->quantizePos(ticks);
            note->quantizeLength(ticks);
        }
        mc->rearrangeAllNotes();
        mc->updateLength();
    }
    Engine::getSong()->setModified();
    return true;
}

int AssistantPanel::parseGridToTicks(const QString& gridStr)
{
    // LMMS uses DefaultTicksPerBar (192) and typically 4/4; 1/16 = 12 ticks
    if (gridStr == "1/2") return TimePos::ticksPerBar() / 2;
    if (gridStr == "1/4") return TimePos::ticksPerBar() / 4;
    if (gridStr == "1/8") return TimePos::ticksPerBar() / 8;
    if (gridStr == "1/16") return TimePos::ticksPerBar() / 16;
    if (gridStr == "1/32") return TimePos::ticksPerBar() / 32;
    return 0;
}

bool AssistantPanel::trySetTempo(const QString& text)
{
    // Patterns: "set tempo 128", "tempo 124 bpm"
    static const QRegularExpression re("(?i)\\btempo\\s*(to\\s*)?(?<bpm>\\d{2,3})");
    const auto m = re.match(text);
    if (!m.hasMatch()) { return false; }
    bool ok = false;
    const int bpm = m.captured("bpm").toInt(&ok);
    if (!ok) { return false; }

    auto song = Engine::getSong();
    if (!song) { return false; }
    song->tempoModel().setValue(std::clamp(bpm, (int)MinTempo, (int)MaxTempo));
    song->setModified();
    return true;
}

bool AssistantPanel::tryTransposeTrack(const QString& text)
{
    // Examples: "transpose Lead -2", "shift Bass down 1", "transpose -1"
    static const QRegularExpression re1("(?i)\\btranspose\\s+(?<name>[A-Za-z0-9_ -]+)?\\s*(?<amt>[-+]?\\d+)");
    static const QRegularExpression re2("(?i)\\bshift\\s+(?<name>[A-Za-z0-9_ -]+)?\\s*(up|down)\\s*(?<n>\\d+)");

    int semitones = 0;
    QString trackName;
    auto m1 = re1.match(text);
    if (m1.hasMatch()) {
        trackName = m1.captured("name").trimmed();
        semitones = m1.captured("amt").toInt();
    } else {
        auto m2 = re2.match(text);
        if (!m2.hasMatch()) { return false; }
        trackName = m2.captured("name").trimmed();
        const int n = m2.captured("n").toInt();
        semitones = text.contains(QRegularExpression("(?i)\\bdown\\b")) ? -n : n;
    }

    InstrumentTrack* it = nullptr;
    if (!trackName.isEmpty()) {
        it = findInstrumentTrackByName(trackName);
    }
    if (!it) { it = defaultInstrumentTrack(); }
    if (!it) { return false; }

    return transposeInstrumentTrack(it, semitones);
}

bool AssistantPanel::tryAddEffect(const QString& text)
{
    // Examples: "add effect Saturation to Lead", "add compressor on Bass"
    static const QRegularExpression re("(?i)\\badd\\s+(an?\\s+)?effect\\s+(?<fx>[A-Za-z0-9_ +-]+)\\s+(to|on)\\s+(?<name>[A-Za-z0-9_ -]+)");
    auto m = re.match(text);
    if (!m.hasMatch()) { return false; }
    const auto fx = m.captured("fx").trimmed();
    const auto trackName = m.captured("name").trimmed();

    auto it = findInstrumentTrackByName(trackName);
    if (!it) { return false; }
    return addEffectToInstrumentTrack(it, fx);
}

InstrumentTrack* AssistantPanel::findInstrumentTrackByName(const QString& name) const
{
    auto song = Engine::getSong();
    if (!song) { return nullptr; }
    for (auto* t : song->tracks()) {
        if (t->type() == Track::Type::Instrument) {
            if (t->name().compare(name, Qt::CaseInsensitive) == 0) {
                return dynamic_cast<InstrumentTrack*>(t);
            }
        }
    }
    return nullptr;
}

InstrumentTrack* AssistantPanel::defaultInstrumentTrack() const
{
    auto song = Engine::getSong();
    if (!song) { return nullptr; }
    for (auto* t : song->tracks()) {
        if (t->type() == Track::Type::Instrument) {
            return dynamic_cast<InstrumentTrack*>(t);
        }
    }
    return nullptr;
}

bool AssistantPanel::transposeInstrumentTrack(InstrumentTrack* track, int semitones)
{
    if (!track) { return false; }
    track->addJournalCheckPoint();
    // Iterate clips; transpose MIDI notes.
    for (auto* clip : track->getClips()) {
        auto* mc = dynamic_cast<MidiClip*>(clip);
        if (!mc) { continue; }
        const auto& notes = mc->notes();
        for (auto* note : notes) {
            note->setKey(note->key() + semitones);
        }
        mc->rearrangeAllNotes();
        mc->updateLength();
    }
    Engine::getSong()->setModified();
    return true;
}

bool AssistantPanel::addEffectToInstrumentTrack(InstrumentTrack* track, const QString& effectNameOrKey)
{
    if (!track) { return false; }
    // Open selection dialog filtered via name; if not interactive, attempt instantiate directly
    // For MVP, instantiate by effect key if matches exactly, else fall back to dialog.
    // Try exact plugin name first
    if (auto* fx = dynamic_cast<Effect*>(Plugin::instantiate(effectNameOrKey, track->audioBusHandle()->effects(), nullptr))) {
        track->audioBusHandle()->effects()->appendEffect(fx);
        return true;
    }

    // Fallback: show selection dialog for user to pick
    EffectSelectDialog dlg(nullptr);
    if (dlg.exec() != QDialog::Accepted) { return false; }
    if (auto* fx2 = dlg.instantiateSelectedPlugin(track->audioBusHandle()->effects())) {
        track->audioBusHandle()->effects()->appendEffect(fx2);
        return true;
    }
    return false;
}

// Simple style macros
static void adjustNoteVelocities(lmms::MidiClip* mc, int delta)
{
    const auto& notes = mc->notes();
    for (auto* note : notes) {
        note->setVolume(std::clamp<volume_t>(note->getVolume() + delta, MinVolume, MaxVolume));
    }
}

bool AssistantPanel::tryStyle(const QString& text)
{
    // Examples: "make Lead more aggressive", "make this track more jazzy"
    static const QRegularExpression re("(?i)\\bmake\\s+(?<name>this\\s+track|[A-Za-z0-9_ -]+)\\s+more\\s+(?<style>aggressive|jazzy)");
    auto m = re.match(text);
    if (!m.hasMatch()) { return false; }
    const auto style = m.captured("style").toLower();
    const auto name = m.captured("name");

    InstrumentTrack* it = nullptr;
    if (name.compare("this track", Qt::CaseInsensitive) == 0) {
        it = defaultInstrumentTrack();
    } else {
        it = findInstrumentTrackByName(name.trimmed());
        if (!it) { it = defaultInstrumentTrack(); }
    }
    if (!it) { return false; }

    it->addJournalCheckPoint();

    // Adjust MIDI velocities slightly for feel
    for (auto* clip : it->getClips()) {
        if (auto* mc = dynamic_cast<MidiClip*>(clip)) {
            if (style == "aggressive") { adjustNoteVelocities(mc, +8); }
            else if (style == "jazzy") { adjustNoteVelocities(mc, -4); }
            mc->rearrangeAllNotes();
        }
    }

    // Add a minimal FX chain by intent
    if (style == "aggressive") {
        addEffectToInstrumentTrack(it, "compressor");
        addEffectToInstrumentTrack(it, "bitcrush");
        addEffectToInstrumentTrack(it, "stereoenhancer");
    } else if (style == "jazzy") {
        addEffectToInstrumentTrack(it, "eq");
        addEffectToInstrumentTrack(it, "reverbsc");
    }

    Engine::getSong()->setModified();
    return true;
}

// Loop/duplicate: "loop 1s to 1m", "repeat this clip to 64 bars", "loop 4 bars across the song"
bool AssistantPanel::tryLoopRepeat(const QString& text)
{
    static const QRegularExpression reTimeRange("(?i)\\b(loop|repeat)\\s+(?<len>(\\d+)(s|sec|seconds|m|min|minutes|bars?))\\s+(to|across|for)\\s+(?<target>(\\d+)(s|sec|seconds|m|min|minutes|bars?))");
    static const QRegularExpression reToMinutes("(?i)\\b(loop|repeat).*(to|for)\\s+(?<target>(\\d+)(s|sec|seconds|m|min|minutes|bars?))");
    auto song = Engine::getSong();
    if (!song) { return false; }

    InstrumentTrack* it = defaultInstrumentTrack();
    if (!it) { return false; }

    auto* srcClip = earliestNonEmptyClip(it);
    if (!srcClip) { return false; }

    // Determine end ticks from the command
    auto parseSpan = [&](const QString& span)->int64_t {
        static const QRegularExpression re("(?i)^(?<n>\\d+)(?<u>s|sec|seconds|m|min|minutes|bars?)$");
        auto m = re.match(span.trimmed());
        if (!m.hasMatch()) return 0;
        const double n = m.captured("n").toDouble();
        const auto u = m.captured("u").toLower();
        if (u.startsWith("s")) return secondsToTicks(n);
        if (u.startsWith("m")) return minutesToTicks(n);
        if (u.startsWith("bar")) return static_cast<int64_t>(n) * TimePos::ticksPerBar();
        return 0;
    };

    int64_t untilTicks = 0;
    auto m1 = reTimeRange.match(text);
    if (m1.hasMatch()) {
        const auto target = m1.captured("target");
        untilTicks = parseSpan(target);
    } else {
        auto m2 = reToMinutes.match(text);
        if (!m2.hasMatch()) { return false; }
        untilTicks = parseSpan(m2.captured("target"));
    }
    if (untilTicks <= 0) { return false; }

    it->addJournalCheckPoint();
    const bool ok = duplicateClipAcrossTicks(it, srcClip, untilTicks);
    if (ok) { song->updateLength(); song->setModified(); }
    return ok;
}

// e.g., "loop the beat 3 times", "repeat this 8 times"
bool AssistantPanel::tryLoopTimes(const QString& text)
{
    static const QRegularExpression re("(?i)\\b(loop|repeat)\\s+(the\\s+beat\\s+)?(?<n>\\d+)\\s+(x|times)\\b");
    auto m = re.match(text);
    if (!m.hasMatch()) return false;
    const int times = m.captured("n").toInt();
    auto* it = defaultInstrumentTrack();
    if (!it) return false;
    auto* src = earliestNonEmptyClip(it);
    if (!src) return false;
    const int clipLen = static_cast<int>(src->length());
    int pos = static_cast<int>(src->startPosition()) + clipLen;
    it->addJournalCheckPoint();
    for (int i = 1; i < times; ++i) {
        auto* clone = src->clone();
        clone->movePosition(pos);
        it->addClip(clone);
        pos += clipLen;
    }
    Engine::getSong()->updateLength();
    Engine::getSong()->setModified();
    log(tr("  -> looped %1 times").arg(times));
    return true;
}

lmms::Clip* AssistantPanel::earliestNonEmptyClip(lmms::Track* track)
{
    if (!track) return nullptr;
    lmms::Clip* best = nullptr;
    for (auto* c : track->getClips()) {
        if (!c) continue;
        if (!best || c->startPosition() < best->startPosition()) {
            best = c;
        }
    }
    return best;
}

bool AssistantPanel::duplicateClipAcrossTicks(lmms::Track* track, lmms::Clip* src, int64_t untilTicks)
{
    if (!track || !src) return false;
    const auto clipLen = static_cast<int>(src->length());
    if (clipLen <= 0) return false;

    // Start from first full block after the source clip start
    int pos = static_cast<int>(src->startPosition()) + clipLen;
    const int endTicks = static_cast<int>(untilTicks);

    while (pos < endTicks) {
        auto* clone = src->clone();
        clone->movePosition(pos);
        track->addClip(clone);
        pos += clipLen;
    }
    return true;
}

int64_t AssistantPanel::minutesToTicks(double minutes)
{
    const auto bpm = Engine::getSong()->getTempo();
    const double ms = minutes * 60.0 * 1000.0;
    const double ticks = ms * bpm / 1250.0; // inverse of ticksToMilliseconds
    return static_cast<int64_t>(ticks);
}

int64_t AssistantPanel::secondsToTicks(double seconds)
{
    return minutesToTicks(seconds / 60.0);
}

// Create a minimal EDM scaffold: kick/hats/claps + bass + lead, tempo set
bool AssistantPanel::tryCreateSampleEdm(const QString& text)
{
    if (!text.contains(QRegularExpression("(?i)create .*edm|make .*edm|sample edm"))) { return false; }
    auto song = Engine::getSong();
    if (!song) { return false; }
    song->tempoModel().setValue(128);

    // Add Kicker (kick)
    auto* kick = addInstrumentTrack("kicker", "Kicker");
    // Add hats (use TripleOscillator with noise-ish preset fallback)
    auto* hats = addInstrumentTrack("tripleoscillator", "Hats");
    // Add claps (sampler or TripleOsc)
    auto* claps = addInstrumentTrack("tripleoscillator", "Claps");
    // Add bass
    auto* bass = addInstrumentTrack("tripleoscillator", "Bass");
    // Add lead
    auto* lead = addInstrumentTrack("tripleoscillator", "Lead");

    const int bar = TimePos::ticksPerBar();
    const int len = 4 * bar; // 4 bars

    // Program simple patterns: this is MVP, just seed notes
    if (kick) {
        auto* mc = ensureMidiClip(kick, 0, len);
        if (mc) {
            // 4-on-the-floor: add step notes each beat
            for (int b = 0; b < 4; ++b) {
                Note n(TimePos(bar / 8), TimePos(b * bar), DefaultMiddleKey - 36); // low kick key
                mc->addNote(n, false);
            }
        }
    }
    if (hats) {
        auto* mc = ensureMidiClip(hats, 0, len);
        if (mc) {
            for (int s = bar / 2; s < len; s += bar) {
                Note n(TimePos(bar / 16), TimePos(s), DefaultMiddleKey + 12);
                mc->addNote(n, false);
            }
        }
    }
    if (claps) {
        auto* mc = ensureMidiClip(claps, 0, len);
        if (mc) {
            // claps on 2 and 4
            for (int b : {1, 3}) {
                Note n(TimePos(bar / 8), TimePos(b * bar), DefaultMiddleKey);
                mc->addNote(n, false);
            }
        }
    }
    if (bass) {
        auto* mc = ensureMidiClip(bass, 0, len);
        if (mc) {
            for (int i = 0; i < 8; ++i) {
                Note n(TimePos(bar / 8), TimePos(i * bar / 2), DefaultMiddleKey - 12);
                mc->addNote(n, false);
            }
        }
    }
    if (lead) {
        auto* mc = ensureMidiClip(lead, 0, len);
        if (mc) {
            for (int i = 0; i < 4; ++i) {
                Note n(TimePos(bar / 4), TimePos(i * bar), DefaultMiddleKey + 7);
                mc->addNote(n, false);
            }
        }
    }

    // Basic FX polish
    if (lead) { addEffectToInstrumentTrack(lead, "stereoenhancer"); }
    if (kick) { addEffectToInstrumentTrack(kick, "compressor"); }

    song->setModified();
    return true;
}

lmms::InstrumentTrack* AssistantPanel::addInstrumentTrack(const QString& pluginName, const QString& displayName)
{
    auto* t = dynamic_cast<InstrumentTrack*>(Track::create(Track::Type::Instrument, Engine::getSong()));
    if (!t) return nullptr;
    t->setName(displayName);
    t->loadInstrument(pluginName);
    return t;
}

lmms::MidiClip* AssistantPanel::ensureMidiClip(lmms::InstrumentTrack* track, int startTicks, int lengthTicks)
{
    if (!track) return nullptr;
    for (auto* c : track->getClips()) {
        if (c && static_cast<int>(c->startPosition()) == startTicks) {
            return dynamic_cast<MidiClip*>(c);
        }
    }
    auto* clip = dynamic_cast<MidiClip*>(track->createClip(TimePos(startTicks)));
    if (!clip) return nullptr;
    clip->changeLength(TimePos(lengthTicks));
    return clip;
}

} // namespace lmms::gui


