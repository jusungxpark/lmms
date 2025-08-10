#include <QApplication>
#include <QMainWindow>
#include <QVBoxLayout>
#include <QPushButton>
#include <QWidget>
#include "AiSidebar.h"

using namespace lmms::gui;

class TestWindow : public QMainWindow
{
    Q_OBJECT

public:
    TestWindow(QWidget* parent = nullptr) : QMainWindow(parent)
    {
        setWindowTitle("LMMS AI Sidebar Test");
        resize(1200, 800);
        
        auto* centralWidget = new QWidget(this);
        setCentralWidget(centralWidget);
        
        auto* layout = new QVBoxLayout(centralWidget);
        
        auto* toggleButton = new QPushButton("Toggle AI Sidebar", this);
        layout->addWidget(toggleButton);
        
        // Create AI Sidebar
        m_aiSidebar = new AiSidebar(this);
        m_aiSidebar->hide();
        
        // Position on the right side
        connect(toggleButton, &QPushButton::clicked, [this]() {
            if (m_aiSidebar->isVisible()) {
                m_aiSidebar->hide();
            } else {
                int x = width() - m_aiSidebar->width();
                int y = 0;
                int h = height();
                m_aiSidebar->setGeometry(x, y, m_aiSidebar->width(), h);
                m_aiSidebar->show();
                m_aiSidebar->raise();
            }
        });
        
        // Handle window resize
        connect(this, &QMainWindow::resizeEvent, [this]() {
            if (m_aiSidebar && m_aiSidebar->isVisible()) {
                int x = width() - m_aiSidebar->width();
                int y = 0;
                int h = height();
                m_aiSidebar->setGeometry(x, y, m_aiSidebar->width(), h);
            }
        });
    }

private:
    AiSidebar* m_aiSidebar;
};

int main(int argc, char* argv[])
{
    QApplication app(argc, argv);
    
    TestWindow window;
    window.show();
    
    return app.exec();
}

#include "test_ai_sidebar.moc"