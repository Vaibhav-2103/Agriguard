import React, { useState, useEffect } from "react";
import { ShieldCheck, Activity, CheckCircle2, XCircle, AlertTriangle, Clock, Users, FileText, ChevronRight } from "lucide-react";
import { api } from "../api";
import { translations } from "../translations";

export default function ExpertDashboard({ onSelectReport, lang }) {
  const [reports, setReports] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterLowCertainty, setFilterLowCertainty] = useState(false);

  const t = translations[lang] || translations.en;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [reps, met] = await Promise.all([
        api.getExpertReports(),
        api.getMetricsSummary()
      ]);
      setReports(reps);
      setMetrics(met);
    } catch (err) {
      console.error("Failed to load expert dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const displayedReports = filterLowCertainty
    ? reports.filter(r => r.status === "completed_low_certainty" || (r.confidence && r.confidence < 0.85))
    : reports;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-100 text-amber-900 rounded-full text-xs font-bold mb-2 border border-amber-300">
            <ShieldCheck className="w-4 h-4 text-amber-700" />
            <span>Agronomist Verification & Verification Queue</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Agricultural Expert Portal
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Audit AI predictions, inspect borderline confidence leaves, and log certified agronomy verdicts.
          </p>
        </div>
      </div>

      {/* Observability Telemetry Cards */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-100 text-emerald-700 rounded-2xl flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium">Success Rate</p>
              <p className="text-lg font-extrabold text-slate-800">{metrics.success_rate_percent}%</p>
            </div>
          </div>

          <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 text-blue-700 rounded-2xl flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium">Avg Inference Time</p>
              <p className="text-lg font-extrabold text-slate-800">{metrics.avg_duration_ms} ms</p>
            </div>
          </div>

          <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 text-purple-700 rounded-2xl flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium">Total Reports</p>
              <p className="text-lg font-extrabold text-slate-800">{metrics.total_reports}</p>
            </div>
          </div>

          <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 text-amber-700 rounded-2xl flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] text-slate-400 font-medium">Registered Farmers</p>
              <p className="text-lg font-extrabold text-slate-800">{metrics.total_users}</p>
            </div>
          </div>
        </div>
      )}

      {/* Review Queue */}
      <div className="bg-white rounded-3xl shadow-sm border border-slate-200 p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-800">
              Crop Diagnosis Review Queue
            </h2>
            <p className="text-xs text-slate-400">
              Select any diagnosis to examine the leaf, overlay heatmap, and post expert feedback.
            </p>
          </div>

          <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700">
            <input
              type="checkbox"
              checked={filterLowCertainty}
              onChange={(e) => setFilterLowCertainty(e.target.checked)}
              className="rounded text-amber-600 focus:ring-amber-500 w-4 h-4"
            />
            <span>Filter Low Certainty Only (&lt;85%)</span>
          </label>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">
            Loading expert queue...
          </div>
        ) : displayedReports.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No pending diagnosis cases in the queue.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {displayedReports.map((r) => (
              <div
                key={r.id}
                onClick={() => onSelectReport(r)}
                className="py-3 px-2 hover:bg-slate-50 rounded-2xl transition cursor-pointer flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <img
                    src={`/${r.image_path}`}
                    alt={r.crop}
                    className="w-12 h-12 rounded-xl object-cover border border-slate-200 flex-shrink-0"
                  />
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-800 truncate">
                      {r.insight?.disease_name || r.predicted_class}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Crop: <strong className="text-slate-600">{r.crop}</strong> | Confidence: {r.confidence ? `${Math.round(r.confidence * 100)}%` : "N/A"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    r.severity === "High" ? "bg-red-100 text-red-800" :
                    r.severity === "Medium" ? "bg-amber-100 text-amber-800" :
                    "bg-emerald-100 text-emerald-800"
                  }`}>
                    {r.severity || "Healthy"}
                  </span>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
