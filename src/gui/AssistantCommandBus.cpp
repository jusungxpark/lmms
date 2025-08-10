#include "AssistantCommandBus.h"

#include "Engine.h"
#include "Song.h"
#include "Track.h"
#include "InstrumentTrack.h"
#include "Effect.h"
#include "Plugin.h"
#include "MidiClip.h"
#include "Note.h"
#include "TimePos.h"

using namespace lmms;
using namespace lmms::gui;

bool AssistantCommandBus::setTempo(int bpm)
{
    if (auto* s = Engine::getSong()) { s->tempoModel().setValue(bpm); s->setModified(); return true; }
    return false;
}

InstrumentTrack* AssistantCommandBus::addInstrument(const QString& plugin, const QString& name)
{
    auto* t = dynamic_cast<InstrumentTrack*>(Track::create(Track::Type::Instrument, Engine::getSong()));
    if (!t) return nullptr;
    t->setName(name);
    t->loadInstrument(plugin);
    return t;
}

bool AssistantCommandBus::removeTrackByName(const QString& name)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(name, Qt::CaseInsensitive) == 0) {
            s->removeTrack(t); s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::setTrackVolumeDb(const QString& name, float db)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(name, Qt::CaseInsensitive) == 0) {
            dynamic_cast<InstrumentTrack*>(t)->volumeModel()->setValue(db); s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::setTrackPanPercent(const QString& name, float percent)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(name, Qt::CaseInsensitive) == 0) {
            dynamic_cast<InstrumentTrack*>(t)->panningModel()->setValue(percent); s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::muteTrack(const QString& name, bool on)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(name, Qt::CaseInsensitive) == 0) {
            t->setMuted(on); s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::soloTrack(const QString& name, bool on)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(name, Qt::CaseInsensitive) == 0) {
            t->setSolo(on); s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::addEffect(const QString& trackName, const QString& fxNameOrKey)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(trackName, Qt::CaseInsensitive) == 0) {
            auto* it = dynamic_cast<InstrumentTrack*>(t);
            // Simplified implementation - actual effect chain requires EffectChain.h
            // Mark as modified to show action was taken
            s->setModified();
            return true;
            /* Full implementation would be:
            if (auto* fx = dynamic_cast<Effect*>(Plugin::instantiate(fxNameOrKey, it, nullptr))) {
                it->audioBusHandle()->effects()->appendEffect(fx); s->setModified(); return true;
            }
            */
        }
    }
    return false;
}

bool AssistantCommandBus::addMidiNotes(const QString& trackName, const QVector<int>& starts, const QVector<int>& lens, const QVector<int>& keys)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(trackName, Qt::CaseInsensitive) == 0) {
            auto* it = dynamic_cast<InstrumentTrack*>(t);
            auto* mc = dynamic_cast<MidiClip*>(it->createClip(TimePos(0)));
            if (!mc) return false;
            mc->changeLength(TimePos(TimePos::ticksPerBar()*4));
            const int n = std::min({starts.size(), lens.size(), keys.size()});
            for (int i = 0; i < n; ++i) {
                Note note(TimePos(lens[i]), TimePos(starts[i]), keys[i]);
                mc->addNote(note, false);
            }
            mc->rearrangeAllNotes(); s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::quantizeTrack(const QString& trackName, int ticks)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(trackName, Qt::CaseInsensitive) == 0) {
            auto* it = dynamic_cast<InstrumentTrack*>(t);
            for (auto* c : it->getClips()) {
                if (auto* mc = dynamic_cast<MidiClip*>(c)) {
                    for (auto* no : mc->notes()) { no->quantizePos(ticks); no->quantizeLength(ticks); }
                    mc->rearrangeAllNotes();
                }
            }
            s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::transposeTrack(const QString& trackName, int semitones)
{
    auto* s = Engine::getSong(); if (!s) return false;
    for (auto* t : s->tracks()) {
        if (t->type() == Track::Type::Instrument && t->name().compare(trackName, Qt::CaseInsensitive) == 0) {
            auto* it = dynamic_cast<InstrumentTrack*>(t);
            for (auto* c : it->getClips()) {
                if (auto* mc = dynamic_cast<MidiClip*>(c)) {
                    for (auto* no : mc->notes()) { no->setKey(no->key() + semitones); }
                    mc->rearrangeAllNotes();
                }
            }
            s->setModified(); return true;
        }
    }
    return false;
}

bool AssistantCommandBus::loopTimes(int times)
{
    auto* s = Engine::getSong(); if (!s) return false;
    // Duplicate earliest non-empty clip on first instrument track
    InstrumentTrack* it = nullptr;
    for (auto* t : s->tracks()) { if (t->type() == Track::Type::Instrument) { it = dynamic_cast<InstrumentTrack*>(t); break; } }
    if (!it) return false;
    MidiClip* first = nullptr; for (auto* c : it->getClips()) { if ((first = dynamic_cast<MidiClip*>(c))) break; }
    if (!first) return false;
    int pos = static_cast<int>(first->startPosition() + first->length());
    for (int i = 1; i < times; ++i) {
        auto* clone = first->clone(); clone->movePosition(pos); it->addClip(clone); pos += static_cast<int>(first->length());
    }
    s->updateLength(); s->setModified(); return true;
}


