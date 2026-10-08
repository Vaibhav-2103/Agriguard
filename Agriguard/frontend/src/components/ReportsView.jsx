import React, { useState, useEffect } from "react";
import { Search, Filter, Trash2, Eye, Calendar, MapPin, Sprout, AlertTriangle, Layers, ChevronRight } from "lucide-react";
import { api } from "../api";
import { translations } from "../translations";

export default function ReportsView({ onSelectReport, lang }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCrop, setSelectedCrop] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("");
  const [supportedCrops, setSupportedCrops] = useState([]);

  const t = translations[lang] || translations.en;

  useEffect(() => {
    loadReports();
    api.getSupportedCrops()
      .then(d => setSupportedCrops(d.crops || []))
      .catch(e => console.error(e));
  }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await api.getReports({
        search: search || undefined,
        crop: selectedCrop || undefined,
        severity: selectedSeverity || undefined
      });
      setReports(data);
    } catch (err) {
      console.error("Failed to load reports:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    loadReports();
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to permanently delete this diagnosis report?")) return;
    try {
      await api.deleteReport(id);
      setReports(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      alert("Failed to delete report");
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-800 tracking-tight">
            {t.navReports}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse and review all past crop disease diagnoses, severity levels and treatments.
          </p>
        </div>
        <div className="text-xs font-semibold text-slate-500 bg-white px-3 py-1.5 rounded-xl border border-slate-200 self-start sm:self-auto">
          Total Records: <strong>{reports.length}</strong>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <form onSubmit={handleFilterSubmit} className="bg-white p-4 rounded-3xl shadow-sm border border-slate-200 flex flex-wrap items-center gap-3">
        {/* Search Input */}
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by disease, crop, or notes..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          />
        </div>

        {/* Crop Select */}
        <select
          value={selectedCrop}
          onChange={(e) => setSelectedCrop(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
        >
          <option value="">All Crops</option>
          {supportedCrops.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        {/* Severity Select */}
        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
        >
          <option value="">All Severities</option>
          <option value="Low">Low (&lt;10%)</option>
          <option value="Medium">Medium (10-30%)</option>
          <option value="High">High (&gt;30%)</option>
        </select>

        <button
          type="submit"
          className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold px-4 py-2 rounded-xl shadow transition"
        >
          Apply Filters
        </button>
      </form>

      {/* Reports Grid */}
      {loading ? (
        <div className="py-20 text-center">
          <div className="w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-500">Loading diagnostic history...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3">
          <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center text-slate-400 mx-auto">
            <Sprout className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-700">No Reports Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            No crop scans match your current filter criteria. Take a new photo of a leaf to begin!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {reports.map((r) => {
            const isHealthy = r.predicted_class && r.predicted_class.toLowerCase().includes("healthy");
            const isNeedBetter = r.status === "needs_better_image";

            return (
              <div
                key={r.id}
                onClick={() => onSelectReport(r)}
                className="bg-white rounded-3xl border border-slate-200/90 shadow-sm hover:shadow-md transition overflow-hidden cursor-pointer flex flex-col justify-between group"
              >
                {/* Image & Badges */}
                <div className="relative aspect-[16/10] bg-slate-900 overflow-hidden">
                  <img
                    src={`/${r.image_path}`}
                    alt={r.crop}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  />
                  <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
                    <span className="bg-slate-900/80 backdrop-blur text-white text-[10px] font-bold px-2 py-0.5 rounded-lg border border-slate-700">
                      {r.crop || "Crop"}
                    </span>
                    {r.severity && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg ${
                        r.severity === "High" ? "bg-red-500 text-white" :
                        r.severity === "Medium" ? "bg-amber-500 text-white" :
                        "bg-emerald-500 text-white"
                      }`}>
                        {r.severity}
                      </span>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-2">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 truncate">
                      {isNeedBetter ? "Photo Quality Issue" : (r.insight?.disease_name || r.predicted_class || "Leaf Scan")}
                    </h3>
                    <p className="text-[11px] text-slate-500 line-clamp-2 mt-0.5">
                      {isNeedBetter ? "Clearer photo required" : (r.insight?.summary || "Diagnosed with local AI model.")}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(r.created_at).toLocaleDateString()}
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={(e) => handleDelete(r.id, e)}
                        className="p-1 hover:text-red-600 transition"
                        title="Delete report"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-700 group-hover:translate-x-0.5 transition" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
