/*
 * AssistantPanel.h - simple NL assistant panel for LMMS
 *
 * Provides a Sidebar panel with a command input that maps
 * natural-language-ish commands to atomic editor actions
 * (e.g., transpose track, set tempo, add effect).
 */

#ifndef LMMS_GUI_ASSISTANT_PANEL_H
#define LMMS_GUI_ASSISTANT_PANEL_H

#include <QWidget>
#include <QRegularExpression>
#include <QStringList>

#include "SideBarWidget.h"

class QListWidget;
class QLineEdit;
class QPushButton;

namespace lmms {
class Track; // forward decl
class Clip;  // forward decl
class InstrumentTrack;
class MidiClip;
class Note;
class Effect;
}

namespace lmms::gui {

class AssistantPanel : public SideBarWidget {
    Q_OBJECT
public:
    explicit AssistantPanel(QWidget* parent);
    ~AssistantPanel() override = default;

private slots:
    void onSubmit();

private:
    bool eventFilter(QObject* obj, QEvent* event) override;
    // Parsing and execution
    void executeCommand(const QString& text);
    bool trySetTempo(const QString& text);
    bool tryTransposeTrack(const QString& text);
    bool tryAddEffect(const QString& text);
    bool tryLoopRepeat(const QString& text);

    // Helpers
    InstrumentTrack* findInstrumentTrackByName(const QString& name) const;
    InstrumentTrack* defaultInstrumentTrack() const;
    bool transposeInstrumentTrack(lmms::InstrumentTrack* track, int semitones);
    bool addEffectToInstrumentTrack(lmms::InstrumentTrack* track, const QString& effectNameOrKey);
    bool tryQuantize(const QString& text);
    static int parseGridToTicks(const QString& gridStr);
    bool tryStyle(const QString& text);
    bool tryCreateSampleEdm(const QString& text);

    // Loop/duplicate helpers
    static class lmms::Clip* earliestNonEmptyClip(lmms::Track* track);
    static bool duplicateClipAcrossTicks(lmms::Track* track, class lmms::Clip* src, int64_t untilTicks);
    static int64_t minutesToTicks(double minutes);
    static int64_t secondsToTicks(double seconds);

    // Creation helpers
    lmms::InstrumentTrack* addInstrumentTrack(const QString& pluginName, const QString& displayName);
    lmms::MidiClip* ensureMidiClip(lmms::InstrumentTrack* track, int startTicks, int lengthTicks);

    // UI
    QListWidget* m_logList {nullptr};
    QLineEdit* m_input {nullptr};
    QPushButton* m_runBtn {nullptr};

    // Command history (like Cursor): Up/Down to navigate
    QStringList m_history;
    int m_historyPos {-1};
};

} // namespace lmms::gui

#endif // LMMS_GUI_ASSISTANT_PANEL_H


