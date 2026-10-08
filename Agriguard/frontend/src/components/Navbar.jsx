import React from "react";
import { Sprout, ShieldAlert, FileText, MessageSquare, LogOut, User as UserIcon, Globe } from "lucide-react";
import { translations } from "../translations";

export default function Navbar({ activeTab, setActiveTab, user, onLogout, lang, setLang }) {
  const t = translations[lang] || translations.en;

  return (
    <header className="bg-emerald-800 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div 
            className="flex items-center gap-3 cursor-pointer select-none"
            onClick={() => setActiveTab("scan")}
          >
            <div className="p-2 bg-emerald-700 rounded-xl shadow-inner flex items-center justify-center">
              <Sprout className="w-7 h-7 text-emerald-300" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                {t.appTitle}
                <span className="text-xs bg-emerald-600/80 text-emerald-100 font-medium px-2 py-0.5 rounded-full border border-emerald-500/40">
                  Local AI
                </span>
              </span>
              <p className="text-[11px] text-emerald-200 hidden sm:block">
                {t.appSubtitle}
              </p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-emerald-900/60 p-1 rounded-xl border border-emerald-700/50">
            <button
              onClick={() => setActiveTab("scan")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "scan"
                  ? "bg-emerald-600 text-white shadow"
                  : "text-emerald-100 hover:bg-emerald-800 hover:text-white"
              }`}
            >
              <Sprout className="w-4 h-4" />
              {t.navHome}
            </button>

            <button
              onClick={() => setActiveTab("reports")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "reports"
                  ? "bg-emerald-600 text-white shadow"
                  : "text-emerald-100 hover:bg-emerald-800 hover:text-white"
              }`}
            >
              <FileText className="w-4 h-4" />
              {t.navReports}
            </button>

            <button
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === "chat"
                  ? "bg-emerald-600 text-white shadow"
                  : "text-emerald-100 hover:bg-emerald-800 hover:text-white"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              {t.navAgriBot}
            </button>

            {user?.role === "expert" && (
              <button
                onClick={() => setActiveTab("expert")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                  activeTab === "expert"
                    ? "bg-amber-600 text-white shadow"
                    : "text-amber-200 hover:bg-amber-900/40 hover:text-white"
                }`}
              >
                <ShieldAlert className="w-4 h-4" />
                {t.navExpert}
              </button>
            )}
          </nav>

          {/* Right Action Area */}
          <div className="flex items-center gap-3">
            {/* Language Switcher */}
            <div className="flex items-center gap-1 bg-emerald-900/80 px-2 py-1 rounded-lg border border-emerald-700 text-xs">
              <Globe className="w-3.5 h-3.5 text-emerald-300" />
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value)}
                className="bg-transparent text-emerald-100 font-medium focus:outline-none cursor-pointer"
              >
                <option value="en" className="text-slate-800">English</option>
                <option value="hi" className="text-slate-800">हिन्दी</option>
                <option value="pa" className="text-slate-800">ਪੰਜਾਬੀ</option>
              </select>
            </div>

            {/* User Profile */}
            {user ? (
              <div className="flex items-center gap-2">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-semibold leading-tight">{user.name}</span>
                  <span className="text-[10px] text-emerald-300 capitalize flex items-center justify-end gap-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${user.role === 'expert' ? 'bg-amber-400' : 'bg-lime-400'}`}></span>
                    {user.role}
                  </span>
                </div>
                <button
                  onClick={onLogout}
                  title="Log out"
                  className="p-2 text-emerald-200 hover:text-white hover:bg-emerald-700 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <div className="md:hidden flex items-center justify-around bg-emerald-900 px-2 py-2 border-t border-emerald-700/60 text-xs">
        <button
          onClick={() => setActiveTab("scan")}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg ${
            activeTab === "scan" ? "text-emerald-300 font-bold" : "text-emerald-100"
          }`}
        >
          <Sprout className="w-4 h-4" />
          <span>{t.navHome}</span>
        </button>
        <button
          onClick={() => setActiveTab("reports")}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg ${
            activeTab === "reports" ? "text-emerald-300 font-bold" : "text-emerald-100"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>{t.navReports}</span>
        </button>
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg ${
            activeTab === "chat" ? "text-emerald-300 font-bold" : "text-emerald-100"
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>{t.navAgriBot}</span>
        </button>
        {user?.role === "expert" && (
          <button
            onClick={() => setActiveTab("expert")}
            className={`flex flex-col items-center gap-1 py-1 px-3 rounded-lg ${
              activeTab === "expert" ? "text-amber-300 font-bold" : "text-amber-200"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>{t.navExpert}</span>
          </button>
        )}
      </div>
    </header>
  );
}
