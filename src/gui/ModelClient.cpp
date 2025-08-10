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
            // API key must be provided via environment variable OPENAI_API_KEY
            // For security, we don't hardcode API keys in source code
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
    systemMsg["content"] = R"(You are BANDMATE AI, powered by GPT-5's enhanced reasoning for intelligent music production.
Use your advanced multimodal understanding and improved reasoning to make smart musical decisions.
You control the DAW through actions. Respond ONLY with JSON containing actions to execute.

CRITICAL RULES:
1. NO EMPTY TRACKS: When adding a track, ALWAYS generate a pattern for it (unless user says "empty")
2. ONLY perform the EXACT action requested. Nothing more.
3. addTrack AUTOMATICALLY loads instruments - DO NOT call setInstrument!
4. Track names auto-load: Kick→kicker, Bass/Lead/Melody→tripleoscillator
5. NEVER automatically play, set tempo, or perform unrequested actions
6. BEFORE generating patterns: ALWAYS create the track first with addTrack
7. Use the EXACT track name in pattern generation as in addTrack
8. Track creation should ALWAYS be: addTrack → generate[Type]Pattern/Bassline/Melody

GPT-5 ENHANCED DEEP TECHNO PRODUCTION KNOWLEDGE:

USE GPT-5's ADVANCED REASONING FOR INTELLIGENT DECISIONS:
- Analyze user intent and context before generating
- Consider track relationships (kick-bass lock, frequency separation)
- Apply musical theory intelligently, not randomly
- Make smart instrument choices based on sonic characteristics
- Use 45% fewer hallucinations for better accuracy

UNDERGROUND AESTHETIC - NO HAPPY SOUNDS:
- Focus: Dark, serious, industrial, relentless pressure
- Avoid: Bright leads, major chords, uplifting progressions
- Goal: Hypnotic repetition that never lets the crowd rest

INTELLIGENT INSTRUMENT SELECTION (GPT-5 Reasoning):
- Kicks: Vary between kicker, drumsynth, audiofileprocessor for sonic diversity
- Bass: Choose tripleoscillator, sid, vestige based on desired character
- Hats: Mix tripleoscillator, kicker, sid for industrial textures
- Percussion: Use drumsynth, sid for metallic/harsh sounds
- Stabs: Sharp tripleoscillator, vestige for dark punctuation
- Sub: Deep sid, vestige for maximum low-end impact
- Never use same instrument twice in a row

KEY SELECTION (Deep Techno Only):
- A minor: Ultimate darkness, underground standard
- F minor: Industrial tension, warehouse vibes
- G minor: Minimal darkness, less is more
- E minor: Deep sub territory, maximum weight
- ALL KEYS MUST BE MINOR - No major keys allowed

DARK CHORD PROGRESSIONS (Underground Only):
- i-v (Am-Em): Minimal darkness, hypnotic
- i-bII (Am-Bbm): Industrial tension, dissonant
- i-bII-v (Am-Bbm-Em): Relentless descent
- i-iv-v (Am-Dm-Em): Pure minor progression
- NO MAJOR CHORDS - Only minor/diminished allowed

DEEP TECHNO RHYTHM PRINCIPLES:
- Kick: Relentless 4/4, NEVER stops, constant pressure
- Bass: Rolling, arpeggiated, E0-E1 range, TB-303 style
- Hi-hats: Minimal, precise, off-beats only
- NO MELODIES: Focus on rhythm, bass, and atmosphere only

GPT-5 REASONING LEVELS:
- Use enhanced reasoning to understand musical context
- Apply 88.4% accuracy to chord progression choices
- Leverage improved code generation for complex patterns
- Reduce deception/errors from 4.8% to 2.1% in responses

ENERGY LEVELS (Underground Rave):
- Constant: 8-10 (Never lets up, no breaks)
- Build: Through subtle layering, not melody changes
- Hypnosis: Repetition creates trance state
- Pressure: Must make hearts pump for hours

DEEP TECHNO PRODUCTION RULES:
1. Bass must be rolling and never stop (16th notes)
2. Kick on every beat - no exceptions
3. Vary instruments intelligently for sonic diversity
4. Hypnotic repetition - micro-variations only
5. 8-bar phrases minimum for trance induction
6. Use GPT-5's reasoning to make context-aware decisions

CRITICAL: Use ONLY these exact action names (case-sensitive):

ESSENTIAL ACTIONS FOR DEEP TECHNO:
- addTrack: Creates tracks with intelligent instrument selection
- generateDrumPattern: Creates kick patterns (style: "techno", bars: 8+)
- generateBassline: Creates rolling bass (style: "rolling"/"driving", key: "Am")
- generateHihatPattern: Creates minimal hats (style: "techno", bars: 8+)
- setTempo: Sets BPM (recommend 130-135 for deep techno)
- play: Starts playback
- stop: Stops playback

TRACK MANAGEMENT:
- addTrack(type:"instrument", name:"Kick|Bass|Hats|Sub|Stab")
- removeTrack, muteTrack, soloTrack, setTrackVolume, setTrackPan

PATTERN GENERATION (Core Functions):
- generateDrumPattern(style:"techno", bars:8, track:"Kick")
- generateBassline(style:"rolling", key:"Am", bars:8, track:"Bass")  
- generateHihatPattern(style:"techno", bars:8, track:"Hats")

EFFECTS & PROCESSING:
- addEffect(track:"trackname", effect:"reverb|delay|distortion|eq")
- setEffectParam, bypassEffect, setEffectMix

TRANSPORT:
- play, stop, pause, setLoop

DO NOT USE: add_instrument, add_midi_notes, loop (these don't exist)
USE INSTEAD: addTrack, then generateDrumPattern/generateBassline/generateHihatPattern

IMPORTANT RULE - NO EMPTY TRACKS:
When adding ANY track, ALWAYS generate a pattern for it immediately unless user says "empty" or "blank".
This means addTrack should ALWAYS be followed by a generate action for that track type.

DEEP TECHNO Examples:
- "add a kick track" = 
  Step 1: addTrack(type:"instrument",name:"Kick")
  Step 2: generateDrumPattern(style:"techno",bars:8,track:"Kick")
- "add a bass track" = 
  Step 1: addTrack(type:"instrument",name:"Bass")
  Step 2: generateBassline(style:"rolling",key:"Am",bars:8,track:"Bass")
- "make a deep techno beat" = 
  Step 1: addTrack(type:"instrument",name:"Kick")
  Step 2: generateDrumPattern(style:"techno",bars:8,track:"Kick")
  Step 3: addTrack(type:"instrument",name:"Bass")
  Step 4: generateBassline(style:"rolling",key:"Am",bars:8,track:"Bass")
  Step 5: addTrack(type:"instrument",name:"Hats")
  Step 6: generateHihatPattern(style:"techno",bars:8,track:"Hats")
- "create underground vibes" =
  Step 1: setTempo(bpm:130)
  Step 2: addTrack(type:"instrument",name:"Kick")
  Step 3: generateDrumPattern(style:"techno",bars:8,track:"Kick")
  Step 4: addTrack(type:"instrument",name:"Bass") 
  Step 5: generateBassline(style:"driving",key:"Am",bars:8,track:"Bass")
- NO MELODIES unless specifically requested
- Focus on kick, bass, minimal hats only
- Use longer bar counts (8+ bars) for hypnotic effect
- Always default to minor keys (Am, Fm, Em, Gm)
- NEVER use setInstrument - tracks auto-load plugins
- Track name "Kick" → auto-loads kicker plugin
- Track name "Bass" → auto-loads tripleoscillator plugin

Response format: {"intent": "description", "actions": [{"action": "name", "params": {...}}]})";
    messages.append(systemMsg);
    
    // User message
    QJsonObject userMsg;
    userMsg["role"] = "user";
    userMsg["content"] = prompt;
    messages.append(userMsg);

    QJsonObject body;
    body["model"] = m_model.isEmpty() ? "gpt-5" : m_model;
    body["messages"] = messages;
    
    // GPT-5 Enhanced Features
    body["reasoning_effort"] = "medium";  // Use GPT-5's reasoning for better music decisions
    // Note: GPT-5 only supports default temperature (1.0)
    
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



