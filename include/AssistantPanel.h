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

#include "SideBarWidget.h"

class QListWidget;
class QLineEdit;
class QPushButton;

namespace lmms {
class Track;
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
    // Parsing and execution
    void executeCommand(const QString& text);
    bool trySetTempo(const QString& text);
    bool tryTransposeTrack(const QString& text);
    bool tryAddEffect(const QString& text);

    // Helpers
    InstrumentTrack* findInstrumentTrackByName(const QString& name) const;
    InstrumentTrack* defaultInstrumentTrack() const;
    bool transposeInstrumentTrack(lmms::InstrumentTrack* track, int semitones);
    bool addEffectToInstrumentTrack(lmms::InstrumentTrack* track, const QString& effectNameOrKey);
    bool tryQuantize(const QString& text);
    static int parseGridToTicks(const QString& gridStr);
    bool tryStyle(const QString& text);

    // UI
    QListWidget* m_logList {nullptr};
    QLineEdit* m_input {nullptr};
    QPushButton* m_runBtn {nullptr};
};

} // namespace lmms::gui

#endif // LMMS_GUI_ASSISTANT_PANEL_H


