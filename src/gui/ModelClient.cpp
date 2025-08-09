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
        emit errorOccurred(tr("No API key configured."));
        return;
    }

    // For now, send a minimal JSON request to OpenAI responses API-compatible endpoint.
    // This is a placeholder; the actual endpoint/path may differ. We'll parse a simple
    // JSON tool plan from the first candidate.
    const QUrl url(QStringLiteral("https://api.openai.com/v1/responses"));
    QNetworkRequest req(url);
    req.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/json"));
    req.setRawHeader("Authorization", QByteArray("Bearer ") + m_apiKey.toUtf8());

    QJsonObject body;
    body["model"] = m_model;
    body["input"] = prompt;

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

void ModelClient::handleReply(QNetworkReply* reply)
{
    if (!reply) { emit errorOccurred(tr("Network error: null reply")); return; }
    const auto status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    const auto data = reply->readAll();
    reply->deleteLater();
    if (status < 200 || status >= 300) {
        emit errorOccurred(QString::fromUtf8(data.isEmpty() ? QByteArray("HTTP error") : data));
        return;
    }
    // Try to extract a plaintext plan (likely JSON text) from Responses API
    QJsonParseError err{};
    const auto doc = QJsonDocument::fromJson(data, &err);
    if (err.error == QJsonParseError::NoError) {
        const auto obj = doc.object();
        const auto outputText = obj.value("output_text").toString();
        if (!outputText.isEmpty()) {
            emit planReady(outputText);
            return;
        }
    }
    // Fallback: emit raw JSON string
    emit planReady(QString::fromUtf8(data));
}



