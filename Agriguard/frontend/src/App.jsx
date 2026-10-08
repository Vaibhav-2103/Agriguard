import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import AuthModal from "./components/AuthModal";
import ScanView from "./components/ScanView";
import ResultView from "./components/ResultView";
import AgriBotView from "./components/AgriBotView";
import ReportsView from "./components/ReportsView";
import ExpertDashboard from "./components/ExpertDashboard";
import { api } from "./api";

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const stored = localStorage.getItem("agriguard_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState("scan");
  const [activeReport, setActiveReport] = useState(null);
  const [lang, setLang] = useState(() => {
    return currentUser?.preferred_language || "en";
  });

  useEffect(() => {
    // Validate session with backend
    const token = localStorage.getItem("agriguard_token");
    if (token) {
      api.getMe()
        .then((user) => {
          setCurrentUser(user);
          if (user.preferred_language) setLang(user.preferred_language);
        })
        .catch(() => {
          api.logout();
          setCurrentUser(null);
        });
    }
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user.preferred_language) setLang(user.preferred_language);
    setActiveTab("scan");
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setActiveReport(null);
    setActiveTab("scan");
  };

  const handleScanComplete = (report) => {
    setActiveReport(report);
    setActiveTab("result");
  };

  const handleSelectReport = (report) => {
    setActiveReport(report);
    setActiveTab("result");
  };

  const handleOpenChat = (report) => {
    setActiveReport(report);
    setActiveTab("chat");
  };

  const handleAddExpertReview = async (reportId, verdict, comment) => {
    const updatedReview = await api.submitExpertReview(reportId, verdict, comment);
    // Refresh active report
    const refreshed = await api.getReport(reportId);
    setActiveReport(refreshed);
    return updatedReview;
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          user={null}
          onLogout={handleLogout}
          lang={lang}
          setLang={setLang}
        />
        <AuthModal onLoginSuccess={handleLoginSuccess} lang={lang} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={currentUser}
        onLogout={handleLogout}
        lang={lang}
        setLang={setLang}
      />

      <main className="flex-1">
        {activeTab === "scan" && (
          <ScanView
            onScanComplete={handleScanComplete}
            onSelectReport={handleSelectReport}
            lang={lang}
          />
        )}

        {activeTab === "result" && (
          <ResultView
            report={activeReport}
            onBackToScan={() => setActiveTab("scan")}
            onOpenChat={handleOpenChat}
            onAddExpertReview={handleAddExpertReview}
            currentUser={currentUser}
            lang={lang}
          />
        )}

        {activeTab === "reports" && (
          <ReportsView
            onSelectReport={handleSelectReport}
            lang={lang}
          />
        )}

        {activeTab === "chat" && (
          <AgriBotView
            activeReport={activeReport}
            onBack={() => setActiveTab(activeReport ? "result" : "scan")}
            lang={lang}
          />
        )}

        {activeTab === "expert" && (
          <ExpertDashboard
            onSelectReport={handleSelectReport}
            lang={lang}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>© 2026 AgriGuard. Free & Open-Source Offline Crop Protection System.</p>
          <p className="flex items-center gap-1.5 text-slate-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            100% Local Inference & SQLite Storage (Zero Cloud APIs)
          </p>
        </div>
      </footer>
    </div>
  );
}
