/*
 * AssistantCommandBus.h - unified command surface for Assistant
 */

#ifndef LMMS_GUI_ASSISTANT_COMMAND_BUS_H
#define LMMS_GUI_ASSISTANT_COMMAND_BUS_H

#include <QString>
#include <QVector>

namespace lmms {
class InstrumentTrack;
}

namespace lmms::gui {

class AssistantCommandBus {
public:
    AssistantCommandBus() = default;

    // Song-level
    bool setTempo(int bpm);

    // Track-level
    lmms::InstrumentTrack* addInstrument(const QString& plugin, const QString& name);
    bool removeTrackByName(const QString& name);
    bool setTrackVolumeDb(const QString& name, float db);
    bool setTrackPanPercent(const QString& name, float percent);
    bool muteTrack(const QString& name, bool on);
    bool soloTrack(const QString& name, bool on);

    // Effects
    bool addEffect(const QString& trackName, const QString& fxNameOrKey);

    // MIDI
    bool addMidiNotes(const QString& trackName, const QVector<int>& starts, const QVector<int>& lens, const QVector<int>& keys);
    bool quantizeTrack(const QString& trackName, int ticks);
    bool transposeTrack(const QString& trackName, int semitones);

    // Loop/duplicate
    bool loopTimes(int times);
};

} // namespace lmms::gui

#endif // LMMS_GUI_ASSISTANT_COMMAND_BUS_H


