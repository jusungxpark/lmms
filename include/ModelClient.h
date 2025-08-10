/*
 * ModelClient.h - interface to an external LLM (e.g., OpenAI GPT-5)
 *
 * Minimal scaffold: stores API key/model and exposes an async complete()
 * that will later call the network. For now, it emits a stub plan or
 * a no-key error. We keep this simple to integrate into AssistantPanel.
 */

#ifndef LMMS_GUI_MODEL_CLIENT_H
#define LMMS_GUI_MODEL_CLIENT_H

#include <QObject>
#include <QString>
#include <QPointer>

class QNetworkAccessManager;
class QNetworkReply;

namespace lmms::gui {

class ModelClient : public QObject {
    Q_OBJECT
public:
    explicit ModelClient(QObject* parent = nullptr);

    void setApiKey(const QString& key) { m_apiKey = key; }
    void setModel(const QString& model) { m_model = model; }
    void setTemperature(double t) { m_temperature = t; }

    // Async entrypoint. In a future commit, perform a real HTTP call and
    // emit planReady() with a JSON plan or tool calls payload.
    void complete(const QString& prompt);
    void cancel();

signals:
    void requestStarted();
    void requestProgress(qint64 bytesReceived, qint64 bytesTotal);
    void requestFinished();
    void planReady(const QString& jsonPlan);
    void errorOccurred(const QString& message);

private:
    void handleReply(QNetworkReply* reply);
    QString m_apiKey;
    QString m_model {"gpt-5"};
    double m_temperature {0.4};
    QPointer<QNetworkAccessManager> m_nam;
    QPointer<QNetworkReply> m_currentReply;
};

} // namespace lmms::gui

#endif // LMMS_GUI_MODEL_CLIENT_H


