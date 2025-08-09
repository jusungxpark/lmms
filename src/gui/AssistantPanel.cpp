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
#include <QRegularExpression>

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
#include "embed.h"

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
    rowLayout->addWidget(m_input);
    rowLayout->addWidget(m_runBtn);
    layout->addWidget(row);

    addContentWidget(root);

    connect(m_runBtn, &QPushButton::clicked, this, &AssistantPanel::onSubmit);
    connect(m_input, &QLineEdit::returnPressed, this, &AssistantPanel::onSubmit);
}

void AssistantPanel::onSubmit()
{
    const auto text = m_input->text().trimmed();
    if (text.isEmpty()) { return; }
    executeCommand(text);
}

void AssistantPanel::executeCommand(const QString& text)
{
    // Try specific parsers in order. If any succeeds, log and return.
    if (trySetTempo(text)) { m_logList->addItem(tr("Set tempo: %1").arg(text)); return; }
    if (tryTransposeTrack(text)) { m_logList->addItem(tr("Transposed: %1").arg(text)); return; }
    if (tryAddEffect(text)) { m_logList->addItem(tr("Added effect: %1").arg(text)); return; }
    if (tryQuantize(text)) { m_logList->addItem(tr("Quantized: %1").arg(text)); return; }
    if (tryStyle(text)) { m_logList->addItem(tr("Applied style: %1").arg(text)); return; }

    m_logList->addItem(tr("Did not understand: %1").arg(text));
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

} // namespace lmms::gui


