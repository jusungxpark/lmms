/*
 * AssistantActions.h - Complete DAW action system for AI Assistant
 * 
 * This defines EVERY possible action in LMMS that the AI can perform.
 * GPT-5 uses these to turn natural language into precise DAW control.
 */

#ifndef LMMS_GUI_ASSISTANT_ACTIONS_H
#define LMMS_GUI_ASSISTANT_ACTIONS_H

#include <QString>
#include <QJsonObject>
#include <QJsonArray>
#include <memory>

namespace lmms {
class Track;
class InstrumentTrack;
class SampleTrack;
class AutomationTrack;
class MidiClip;
class AutomationClip;
class Note;
class Plugin;
}

namespace lmms::gui {

// Action result for feedback to GPT
struct ActionResult {
    bool success;
    QString message;
    QJsonObject data;  // Optional return data
};

class AssistantActions {
public:
    AssistantActions();
    ~AssistantActions();

    // Execute any action by name with parameters
    ActionResult execute(const QString& action, const QJsonObject& params);

    // === FILE OPERATIONS ===
    ActionResult newProject(const QJsonObject& params);
    ActionResult openProject(const QJsonObject& params);  // {path: string}
    ActionResult saveProject(const QJsonObject& params);  // {path?: string}
    ActionResult exportAudio(const QJsonObject& params);  // {path: string, format: wav|mp3|ogg|flac}
    ActionResult exportMidi(const QJsonObject& params);   // {path: string}
    ActionResult exportStems(const QJsonObject& params);  // {path: string}
    ActionResult importAudio(const QJsonObject& params);  // {path: string, track?: string}
    ActionResult importMidi(const QJsonObject& params);   // {path: string}

    // === PROJECT SETTINGS ===
    ActionResult setTempo(const QJsonObject& params);     // {bpm: number}
    ActionResult setTimeSignature(const QJsonObject& params); // {numerator: number, denominator: number}
    ActionResult setMasterVolume(const QJsonObject& params);  // {volume: 0-200}
    ActionResult setMasterPitch(const QJsonObject& params);   // {pitch: -24 to 24}
    ActionResult setSwing(const QJsonObject& params);     // {amount: 0-100}
    ActionResult setPlaybackPosition(const QJsonObject& params); // {bar: number, beat?: number}

    // === TRACK OPERATIONS ===
    ActionResult addTrack(const QJsonObject& params);     // {type: instrument|sample|automation, name: string}
    ActionResult removeTrack(const QJsonObject& params);  // {name: string}
    ActionResult renameTrack(const QJsonObject& params);  // {oldName: string, newName: string}
    ActionResult muteTrack(const QJsonObject& params);    // {name: string, mute: bool}
    ActionResult soloTrack(const QJsonObject& params);    // {name: string, solo: bool}
    ActionResult setTrackVolume(const QJsonObject& params);   // {name: string, volume: 0-200}
    ActionResult setTrackPan(const QJsonObject& params);      // {name: string, pan: -100 to 100}
    ActionResult setTrackPitch(const QJsonObject& params);    // {name: string, pitch: -24 to 24}
    ActionResult duplicateTrack(const QJsonObject& params);   // {name: string}
    ActionResult moveTrack(const QJsonObject& params);    // {name: string, position: number}
    ActionResult setTrackColor(const QJsonObject& params);    // {name: string, color: hex}

    // === INSTRUMENT OPERATIONS ===
    ActionResult setInstrument(const QJsonObject& params);    // {track: string, plugin: string}
    ActionResult loadPreset(const QJsonObject& params);   // {track: string, preset: string}
    ActionResult savePreset(const QJsonObject& params);   // {track: string, name: string}
    ActionResult setInstrumentParam(const QJsonObject& params); // {track: string, param: string, value: number}
    ActionResult randomizeInstrument(const QJsonObject& params); // {track: string}

    // === MIDI/PATTERN OPERATIONS ===
    ActionResult addMidiClip(const QJsonObject& params);  // {track: string, bar: number, length: bars}
    ActionResult removeMidiClip(const QJsonObject& params); // {track: string, bar: number}
    ActionResult addNote(const QJsonObject& params);      // {track: string, clip?: number, key: 0-127, start: ticks, length: ticks, velocity: 0-127}
    ActionResult removeNote(const QJsonObject& params);   // {track: string, clip?: number, key: number, start: ticks}
    ActionResult clearNotes(const QJsonObject& params);   // {track: string, clip?: number}
    ActionResult transposeNotes(const QJsonObject& params); // {track: string, semitones: number, clip?: number}
    ActionResult quantizeNotes(const QJsonObject& params);  // {track: string, grid: 1/4|1/8|1/16|1/32, clip?: number}
    ActionResult humanizeNotes(const QJsonObject& params);  // {track: string, timing: 0-100, velocity: 0-100}
    ActionResult scaleVelocity(const QJsonObject& params);  // {track: string, scale: 0-200}
    ActionResult reverseNotes(const QJsonObject& params);   // {track: string, clip?: number}
    ActionResult generateChord(const QJsonObject& params);  // {track: string, root: 0-127, type: maj|min|7|maj7|min7|dim|aug, position: ticks}
    ActionResult generateScale(const QJsonObject& params);  // {track: string, root: 0-127, scale: major|minor|pentatonic|blues, octaves: 1-4}
    ActionResult generateArpeggio(const QJsonObject& params); // {track: string, pattern: up|down|updown|random, rate: 1/4|1/8|1/16}

    // === AUDIO/SAMPLE OPERATIONS ===
    ActionResult addSampleClip(const QJsonObject& params);  // {track: string, file: path, bar: number}
    ActionResult trimSample(const QJsonObject& params);     // {track: string, clip: number, start: ms, end: ms}
    ActionResult reverseSample(const QJsonObject& params);  // {track: string, clip: number}
    ActionResult pitchSample(const QJsonObject& params);    // {track: string, clip: number, semitones: number}
    ActionResult timeStretchSample(const QJsonObject& params); // {track: string, clip: number, factor: 0.5-2.0}
    ActionResult chopSample(const QJsonObject& params);     // {track: string, clip: number, slices: number}
    ActionResult fadeIn(const QJsonObject& params);         // {track: string, clip: number, duration: ms}
    ActionResult fadeOut(const QJsonObject& params);        // {track: string, clip: number, duration: ms}

    // === EFFECTS OPERATIONS ===
    ActionResult addEffect(const QJsonObject& params);      // {track: string, effect: string, position?: number}
    ActionResult removeEffect(const QJsonObject& params);   // {track: string, position: number}
    ActionResult setEffectParam(const QJsonObject& params); // {track: string, effect: number, param: string, value: number}
    ActionResult bypassEffect(const QJsonObject& params);   // {track: string, effect: number, bypass: bool}
    ActionResult setEffectMix(const QJsonObject& params);   // {track: string, effect: number, mix: 0-100}
    ActionResult loadEffectPreset(const QJsonObject& params); // {track: string, effect: number, preset: string}
    ActionResult reorderEffects(const QJsonObject& params); // {track: string, from: number, to: number}

    // === MIXER OPERATIONS ===
    ActionResult setSend(const QJsonObject& params);        // {track: string, send: number, amount: 0-100}
    ActionResult setMixerChannel(const QJsonObject& params); // {track: string, channel: number}
    ActionResult addMixerEffect(const QJsonObject& params); // {channel: number, effect: string}
    ActionResult linkTracks(const QJsonObject& params);     // {tracks: [string]}
    ActionResult groupTracks(const QJsonObject& params);    // {tracks: [string], name: string}

    // === AUTOMATION OPERATIONS ===
    ActionResult addAutomation(const QJsonObject& params);  // {param: string, track?: string}
    ActionResult addAutomationPoint(const QJsonObject& params); // {track: string, time: ticks, value: 0-1}
    ActionResult clearAutomation(const QJsonObject& params); // {track: string, param: string}
    ActionResult setAutomationMode(const QJsonObject& params); // {mode: linear|cubic|step}
    ActionResult recordAutomation(const QJsonObject& params); // {enable: bool}
    ActionResult addLFO(const QJsonObject& params);         // {target: string, rate: hz, amount: 0-100, shape: sine|square|saw|triangle}
    ActionResult addEnvelope(const QJsonObject& params);    // {target: string, attack: ms, decay: ms, sustain: 0-100, release: ms}

    // === ARRANGEMENT OPERATIONS ===
    ActionResult copyClips(const QJsonObject& params);      // {track: string, from: bar, to: bar}
    ActionResult pasteClips(const QJsonObject& params);     // {track: string, at: bar}
    ActionResult cutClips(const QJsonObject& params);       // {track: string, from: bar, to: bar}
    ActionResult splitClip(const QJsonObject& params);      // {track: string, at: bar.beat}
    ActionResult mergeClips(const QJsonObject& params);     // {track: string, from: bar, to: bar}
    ActionResult duplicateClips(const QJsonObject& params); // {track: string, times: number}
    ActionResult loopClips(const QJsonObject& params);      // {track: string, start: bar, end: bar}
    ActionResult moveClips(const QJsonObject& params);      // {track: string, by: bars}
    ActionResult resizeClip(const QJsonObject& params);     // {track: string, clip: number, newLength: bars}

    // === TRANSPORT OPERATIONS ===
    ActionResult play(const QJsonObject& params);           // {}
    ActionResult stop(const QJsonObject& params);           // {}
    ActionResult pause(const QJsonObject& params);          // {}
    ActionResult record(const QJsonObject& params);         // {mode: overwrite|merge|layer}
    ActionResult setLoop(const QJsonObject& params);        // {start: bar, end: bar, enable: bool}
    ActionResult setPunch(const QJsonObject& params);       // {in: bar, out: bar, enable: bool}
    ActionResult setMetronome(const QJsonObject& params);   // {enable: bool, volume: 0-100}
    ActionResult tapTempo(const QJsonObject& params);       // {}
    ActionResult countIn(const QJsonObject& params);        // {bars: 1|2|4}

    // === ADVANCED OPERATIONS ===
    ActionResult analyzeTempo(const QJsonObject& params);   // {track: string}
    ActionResult analyzeKey(const QJsonObject& params);     // {track: string}
    ActionResult detectChords(const QJsonObject& params);   // {track: string}
    ActionResult groove(const QJsonObject& params);         // {template: string, amount: 0-100}
    ActionResult sidechain(const QJsonObject& params);      // {source: string, target: string, amount: 0-100}
    ActionResult vocode(const QJsonObject& params);         // {carrier: string, modulator: string}
    ActionResult freeze(const QJsonObject& params);         // {track: string}
    ActionResult bounce(const QJsonObject& params);         // {tracks: [string], to: string}

    // === CREATIVE OPERATIONS ===
    ActionResult generateDrumPattern(const QJsonObject& params); // {style: house|trap|dnb|jazz, bars: number, track?: string}
    ActionResult generateHihatPattern(const QJsonObject& params); // {style: house|trap|steady, bars: number, track?: string}
    ActionResult generateBassline(const QJsonObject& params);    // {style: walking|808|reese|sub, key: string, bars: number, track?: string}
    ActionResult generateMelody(const QJsonObject& params);      // {scale: string, style: catchy|ambient|complex, bars: number}
    ActionResult generateHarmony(const QJsonObject& params);     // {progression: string, voicing: close|open|jazz}
    ActionResult generateChords(const QJsonObject& params);      // {key: string, progression: string, style: string, bars: number}
    ActionResult applyStyle(const QJsonObject& params);          // {style: aggressive|smooth|vintage|modern}
    ActionResult randomize(const QJsonObject& params);           // {target: track|pattern|effect, amount: 0-100}

    // === VIEW OPERATIONS ===
    ActionResult zoomIn(const QJsonObject& params);         // {amount?: number}
    ActionResult zoomOut(const QJsonObject& params);        // {amount?: number}
    ActionResult fitToScreen(const QJsonObject& params);    // {}
    ActionResult showMixer(const QJsonObject& params);      // {show: bool}
    ActionResult showPianoRoll(const QJsonObject& params);  // {track: string}
    ActionResult showAutomation(const QJsonObject& params); // {track: string}
    ActionResult setGridSnap(const QJsonObject& params);    // {snap: off|bar|beat|1/8|1/16|1/32}

private:
    class Impl;
    std::unique_ptr<Impl> m_impl;
};

} // namespace lmms::gui

#endif // LMMS_GUI_ASSISTANT_ACTIONS_H