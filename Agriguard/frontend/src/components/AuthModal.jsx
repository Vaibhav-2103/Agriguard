import React, { useState } from "react";
import { Sprout, User, Lock, Mail, CheckCircle2, ShieldCheck } from "lucide-react";
import { api } from "../api";
import { translations } from "../translations";

export default function AuthModal({ onLoginSuccess, lang }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("farmer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const t = translations[lang] || translations.en;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        const data = await api.register(name, email, password, role, lang);
        onLoginSuccess(data.user);
      } else {
        const data = await api.login(email, password);
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  // Quick Demo Logins
  const handleDemoLogin = async (demoRole) => {
    setError("");
    setLoading(true);
    const demoEmail = demoRole === "expert" ? "expert@agriguard.in" : "ramesh@farmer.in";
    const demoPass = "pass1234password";

    try {
      try {
        const data = await api.login(demoEmail, demoPass);
        onLoginSuccess(data.user);
      } catch (loginErr) {
        // If not seeded yet, register automatically
        const demoName = demoRole === "expert" ? "Dr. M. S. Swaminathan" : "Ramesh Kumar";
        const regData = await api.register(demoName, demoEmail, demoPass, demoRole, lang);
        onLoginSuccess(regData.user);
      }
    } catch (err) {
      setError(err.message || "Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl border border-slate-200/80 max-w-md w-full p-8 relative overflow-hidden">
        {/* Top green accent */}
        <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600" />

        {/* Header Icon */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center text-emerald-700 shadow-sm mb-3">
            <Sprout className="w-9 h-9" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">
            {isRegister ? "Join AgriGuard" : "Welcome Back"}
          </h2>
          <p className="text-sm text-slate-500 mt-1 max-w-xs">
            {isRegister
              ? "Create your local farm account for crop diagnosis & IPM plans"
              : "Access your crop health scans, severity insights & AgriBot"}
          </p>
        </div>

        {/* Demo Fast Login Buttons */}
        <div className="bg-emerald-50/70 border border-emerald-200/70 rounded-2xl p-3 mb-6">
          <p className="text-xs font-semibold text-emerald-900 mb-2 text-center uppercase tracking-wider">
            ⚡ Quick 1-Click Demo Login
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() => handleDemoLogin("farmer")}
              className="flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-2 px-3 rounded-xl shadow-sm transition active:scale-95 disabled:opacity-50"
            >
              <Sprout className="w-3.5 h-3.5" />
              Farmer Mode
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => handleDemoLogin("expert")}
              className="flex items-center justify-center gap-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold py-2 px-3 rounded-xl shadow-sm transition active:scale-95 disabled:opacity-50"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Expert Mode
            </button>
          </div>
        </div>

        {/* Tab switch */}
        <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setError(""); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
              !isRegister ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setError(""); }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
              isRegister ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ramesh Kumar"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@farm.in"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Role</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRole("farmer")}
                  className={`p-2.5 border rounded-xl text-xs font-medium text-center transition flex items-center justify-center gap-1.5 ${
                    role === "farmer"
                      ? "border-emerald-500 bg-emerald-50 text-emerald-800 font-semibold"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <Sprout className="w-3.5 h-3.5 text-emerald-600" />
                  Farmer
                </button>
                <button
                  type="button"
                  onClick={() => setRole("expert")}
                  className={`p-2.5 border rounded-xl text-xs font-medium text-center transition flex items-center justify-center gap-1.5 ${
                    role === "expert"
                      ? "border-amber-500 bg-amber-50 text-amber-800 font-semibold"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
                  Agricultural Expert
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold py-3 px-4 rounded-xl shadow-md transition active:scale-[0.99] disabled:opacity-60 text-sm"
          >
            {loading ? "Processing..." : isRegister ? "Create Free Account" : "Sign In to AgriGuard"}
          </button>
        </form>

        <p className="text-[11px] text-center text-slate-400 mt-6">
          Protected by local SQLite database. No external cloud or paid AI APIs.
        </p>
      </div>
    </div>
  );
}
