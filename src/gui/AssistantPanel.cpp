/*
 * AssistantPanel.cpp - NL assistant panel for LMMS
 */

#include "AssistantPanel.h"

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

AssistantPanel::AssistantPanel(QWidget* parent)
    : SideBarWidget(tr("Assistant"), embed::getIconPixmap("help"), parent)
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
    connect(m_modelClient, &ModelClient::requestProgress, this, [this](qint64 rec, qint64 tot){
        if (tot > 0) {
            m_logList->addItem(tr("Received %1/%2 bytes").arg(rec).arg(tot));
        } else {
            m_logList->addItem(tr("Received %1 bytes").arg(rec));
        }
        m_logList->scrollToBottom();
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
    if (!maybeInvokeModel(text)) {
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
    if (trySetTempo(text)) { m_logList->addItem(tr("Set tempo: %1").arg(text)); m_logList->scrollToBottom(); return; }
    if (tryTransposeTrack(text)) { m_logList->addItem(tr("Transposed: %1").arg(text)); m_logList->scrollToBottom(); return; }
    if (tryAddEffect(text)) { m_logList->addItem(tr("Added effect: %1").arg(text)); m_logList->scrollToBottom(); return; }
    if (tryQuantize(text)) { m_logList->addItem(tr("Quantized: %1").arg(text)); m_logList->scrollToBottom(); return; }
    if (tryStyle(text)) { m_logList->addItem(tr("Applied style: %1").arg(text)); m_logList->scrollToBottom(); return; }
    if (tryLoopRepeat(text)) { m_logList->addItem(tr("Looped/repeated: %1").arg(text)); m_logList->scrollToBottom(); return; }
    if (tryCreateSampleEdm(text)) { m_logList->addItem(tr("Created sample EDM setup: %1").arg(text)); m_logList->scrollToBottom(); return; }

    m_logList->addItem(tr("Did not understand: %1").arg(text));
    m_logList->scrollToBottom();
}

bool AssistantPanel::maybeInvokeModel(const QString& text)
{
    if (!m_aiToggle || !m_aiToggle->isChecked()) return false;
    if (!m_modelClient) return false;
    // For now, send everything that isn't matched by fast-path keywords
    const bool looksComplex = !text.contains(QRegularExpression("(?i)^(tempo|transpose|quantize|add|loop|repeat)"));
    if (!looksComplex) return false;
    const auto prompt = buildPlannerPrompt(text);
    m_modelClient->complete(prompt);
    // log handled by requestStarted/Progress
    return true;
}

QString AssistantPanel::buildPlannerPrompt(const QString& userText) const
{
    // Provide a short system prompt with available tools summary.
    QString tools = R"(You are a music production assistant inside LMMS.
You can do these actions via a planner that emits JSON with a list of steps.
Each step has: {"action": "set_tempo|add_instrument|add_effect|add_midi_notes|transpose|quantize|loop|route|sidechain", ...}.)";
    return tools + "\nUser: " + userText;
}

void AssistantPanel::handleModelPlan(const QString& responseJson)
{
    // Expect an OpenAI responses JSON. Try to extract a JSON object from content.
    QJsonParseError err{};
    const auto doc = QJsonDocument::fromJson(responseJson.toUtf8(), &err);
    if (err.error != QJsonParseError::NoError) {
        m_logList->addItem(tr("Model parse error: %1").arg(err.errorString()));
        m_logList->scrollToBottom();
        return;
    }
    // Heuristic: if it contains {"plan": {"steps": [...]}} then run steps
    QJsonObject root = doc.object();
    QJsonObject plan = root.value("plan").toObject();
    QJsonArray steps = plan.value("steps").toArray();
    if (steps.isEmpty()) {
        // Some models return {"output_text": "..."} or {"content":[...]}
        m_logList->addItem(tr("Model responded, but no steps found. Using local fallback."));
        // Fallback: seed a sample EDM scaffold so user gets immediate output
        tryCreateSampleEdm(QStringLiteral("sample edm"));
        m_logList->scrollToBottom();
        return;
    }
    int applied = 0;
    for (const auto& v : steps) {
        const auto o = v.toObject();
        const auto action = o.value("action").toString();
        if (action == "set_tempo") {
            const int bpm = o.value("bpm").toInt();
            if (bpm > 0) { Engine::getSong()->tempoModel().setValue(bpm); applied++; }
        } else if (action == "add_instrument") {
            const auto plugin = o.value("plugin").toString();
            const auto name = o.value("name").toString(plugin);
            addInstrumentTrack(plugin, name);
            applied++;
        } else if (action == "add_effect") {
            const auto track = o.value("track").toString();
            const auto fx = o.value("fx").toString();
            if (auto* it = findInstrumentTrackByName(track)) { addEffectToInstrumentTrack(it, fx); applied++; }
        } else if (action == "transpose") {
            const auto track = o.value("track").toString();
            const int semitones = o.value("semitones").toInt();
            InstrumentTrack* it = track.isEmpty() ? defaultInstrumentTrack() : findInstrumentTrackByName(track);
            if (it) { transposeInstrumentTrack(it, semitones); applied++; }
        } else if (action == "quantize") {
            const auto grid = o.value("grid").toString("1/16");
            tryQuantize(QStringLiteral("quantize %1").arg(grid));
            applied++;
        } else if (action == "loop") {
            const auto span = o.value("span").toString("4bars");
            tryLoopRepeat(QStringLiteral("loop %1 across song").arg(span));
            applied++;
        }
    }
    Engine::getSong()->setModified();
    m_logList->addItem(tr("Applied %1 model steps").arg(applied));
    m_logList->scrollToBottom();
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


