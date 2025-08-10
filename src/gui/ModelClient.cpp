#include "ModelClient.h"

#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QUrl>
#include <QUrlQuery>

using namespace lmms::gui;

ModelClient::ModelClient(QObject* parent)
    : QObject(parent)
    , m_nam(new QNetworkAccessManager(this))
{
}

void ModelClient::complete(const QString& prompt)
{
    if (m_apiKey.isEmpty()) {
        // Try to load from environment (like Cursor does)
        m_apiKey = QString::fromUtf8(qgetenv("OPENAI_API_KEY"));
        if (m_apiKey.isEmpty()) {
            emit errorOccurred(tr("No API key configured. Set OPENAI_API_KEY environment variable."));
            return;
        }
    }

    // Use the correct OpenAI Chat Completions API (like Cursor)
    const QUrl url(QStringLiteral("https://api.openai.com/v1/chat/completions"));
    QNetworkRequest req(url);
    req.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/json"));
    req.setRawHeader("Authorization", QByteArray("Bearer ") + m_apiKey.toUtf8());

    // Build the messages array with system context
    QJsonArray messages;
    
    // System message - tells GPT how to behave (like Cursor)
    QJsonObject systemMsg;
    systemMsg["role"] = "system";
    systemMsg["content"] = R"(You are BANDMATE AI, a music production assistant integrated into LMMS DAW.
You control EVERY aspect of the DAW through actions. Respond ONLY with JSON containing actions to execute.

Available actions (use these exact names):
FILE: newProject, openProject, saveProject, exportAudio, exportMidi, exportStems, importAudio, importMidi
SETTINGS: setTempo(bpm), setTimeSignature(numerator,denominator), setMasterVolume, setMasterPitch, setSwing, setPlaybackPosition
TRACKS: addTrack(type,name), removeTrack, renameTrack, muteTrack, soloTrack, setTrackVolume, setTrackPan, setTrackPitch, duplicateTrack, moveTrack, setTrackColor
INSTRUMENTS: setInstrument, loadPreset, savePreset, setInstrumentParam, randomizeInstrument
MIDI: addMidiClip, removeMidiClip, addNote, removeNote, clearNotes, transposeNotes, quantizeNotes, humanizeNotes, scaleVelocity, reverseNotes, generateChord, generateScale, generateArpeggio
AUDIO: addSampleClip, trimSample, reverseSample, pitchSample, timeStretchSample, chopSample, fadeIn, fadeOut
EFFECTS: addEffect, removeEffect, setEffectParam, bypassEffect, setEffectMix, loadEffectPreset, reorderEffects
MIXER: setSend, setMixerChannel, addMixerEffect, linkTracks, groupTracks
AUTOMATION: addAutomation, addAutomationPoint, clearAutomation, setAutomationMode, recordAutomation, addLFO, addEnvelope
ARRANGEMENT: copyClips, pasteClips, cutClips, splitClip, mergeClips, duplicateClips, loopClips, moveClips, resizeClip
TRANSPORT: play, stop, pause, record, setLoop, setPunch, setMetronome, tapTempo, countIn
ANALYSIS: analyzeTempo, analyzeKey, detectChords, groove, sidechain, vocode, freeze, bounce
CREATIVE: generateDrumPattern(style,bars), generateBassline(style,key,bars), generateMelody(scale,style,bars), generateHarmony, applyStyle, randomize
VIEW: zoomIn, zoomOut, fitToScreen, showMixer, showPianoRoll, showAutomation, setGridSnap

Response format: {"intent": "description", "actions": [{"action": "name", "params": {...}}]})";
    messages.append(systemMsg);
    
    // User message
    QJsonObject userMsg;
    userMsg["role"] = "user";
    userMsg["content"] = prompt;
    messages.append(userMsg);

    QJsonObject body;
    body["model"] = m_model.isEmpty() ? "gpt-4" : m_model;
    body["messages"] = messages;
    body["temperature"] = m_temperature;
    
    // Request JSON response format
    QJsonObject responseFormat;
    responseFormat["type"] = "json_object";
    body["response_format"] = responseFormat;

    const auto payload = QJsonDocument(body).toJson();
    if (m_currentReply) { m_currentReply->abort(); m_currentReply->deleteLater(); }
    m_currentReply = m_nam->post(req, payload);
    emit requestStarted();
    connect(m_currentReply, &QNetworkReply::downloadProgress, this, &ModelClient::requestProgress);
    connect(m_currentReply, &QNetworkReply::finished, this, [this]() {
        emit requestFinished();
        handleReply(m_currentReply);
        m_currentReply = nullptr;
    });
}

void ModelClient::cancel()
{
    if (m_currentReply) {
        m_currentReply->abort();
        m_currentReply->deleteLater();
        m_currentReply = nullptr;
    }
}

void ModelClient::handleReply(QNetworkReply* reply)
{
    if (!reply) { emit errorOccurred(tr("Network error: null reply")); return; }
    const auto status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    const auto data = reply->readAll();
    reply->deleteLater();
    
    if (status < 200 || status >= 300) {
        // Parse error message from OpenAI API
        QJsonParseError err{};
        const auto doc = QJsonDocument::fromJson(data, &err);
        if (err.error == QJsonParseError::NoError) {
            const auto obj = doc.object();
            const auto error = obj.value("error").toObject();
            const auto message = error.value("message").toString();
            if (!message.isEmpty()) {
                emit errorOccurred(tr("API Error: %1").arg(message));
                return;
            }
        }
        emit errorOccurred(QString::fromUtf8(data.isEmpty() ? QByteArray("HTTP error") : data));
        return;
    }
    
    // Parse the OpenAI Chat Completions response
    QJsonParseError err{};
    const auto doc = QJsonDocument::fromJson(data, &err);
    if (err.error != QJsonParseError::NoError) {
        emit errorOccurred(tr("Invalid JSON response: %1").arg(err.errorString()));
        return;
    }
    
    const auto obj = doc.object();
    const auto choices = obj.value("choices").toArray();
    
    if (!choices.isEmpty()) {
        const auto firstChoice = choices[0].toObject();
        const auto message = firstChoice.value("message").toObject();
        const auto content = message.value("content").toString();
        
        if (!content.isEmpty()) {
            // The content should be JSON since we requested JSON format
            emit planReady(content);
            return;
        }
    }
    
    // Fallback: emit raw response
    emit errorOccurred(tr("Unexpected API response format"));
}



