import React, { useState, useRef, useEffect } from "react";
import { Upload, Camera, Sprout, AlertCircle, Info, CheckCircle2, ChevronRight, Sparkles, Image as ImageIcon } from "lucide-react";
import { api } from "../api";
import { translations } from "../translations";

export default function ScanView({ onScanComplete, lang, onSelectReport }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [crop, setCrop] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  
  const [supportedCrops, setSupportedCrops] = useState([]);
  const [showCropsModal, setShowCropsModal] = useState(false);
  const [recentReports, setRecentReports] = useState([]);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const t = translations[lang] || translations.en;

  useEffect(() => {
    // Load supported crops
    api.getSupportedCrops()
      .then((data) => setSupportedCrops(data.crops || []))
      .catch((err) => console.error("Error loading crops:", err));

    // Load recent reports
    api.getReports()
      .then((data) => setRecentReports(data.slice(0, 3)))
      .catch((err) => console.error("Error loading recent reports:", err));
  }, []);

  const handleFileChange = (selectedFile) => {
    if (!selectedFile) return;
    setError("");
    setFile(selectedFile);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result);
    reader.readAsDataURL(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleScanSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select or capture a leaf photo first.");
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("image", file);
    if (crop) formData.append("crop", crop);
    if (location) formData.append("location", location);
    if (notes) formData.append("notes", notes);

    try {
      const report = await api.uploadReport(formData);
      onScanComplete(report);
    } catch (err) {
      setError(err.message || "Failed to analyze leaf image");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Title Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-semibold mb-3 border border-emerald-200">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
          <span>Local MobileNetV2 Deep Learning & OpenCV Vision</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-800 tracking-tight">
          {t.scanTitle}
        </h1>
        <p className="text-base text-slate-600 max-w-xl mx-auto mt-2">
          {t.scanSubtitle}
        </p>

        {/* Supported Crops trigger */}
        <div className="mt-3 flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={() => setShowCropsModal(true)}
            className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold underline decoration-dotted flex items-center gap-1"
          >
            <Info className="w-3.5 h-3.5" />
            <span>View 14 Supported Crops & Model Limitations</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl flex items-start gap-3 shadow-sm">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold">Diagnosis Notice</p>
            <p className="text-xs mt-0.5 text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Upload & Form Container */}
      <div className="bg-white rounded-3xl shadow-md border border-slate-200/80 p-6 sm:p-8">
        <form onSubmit={handleScanSubmit} className="space-y-6">
          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-3xl p-8 text-center transition flex flex-col items-center justify-center cursor-pointer relative ${
              isDragging
                ? "border-emerald-500 bg-emerald-50"
                : preview
                ? "border-emerald-300 bg-slate-50/50"
                : "border-slate-300 hover:border-emerald-500 bg-slate-50/50 hover:bg-emerald-50/30"
            }`}
            onClick={() => !preview && fileInputRef.current?.click()}
          >
            {preview ? (
              <div className="relative group w-full flex flex-col items-center">
                <img
                  src={preview}
                  alt="Leaf Preview"
                  className="max-h-72 w-auto object-contain rounded-2xl shadow-md border border-slate-200"
                />
                <div className="mt-4 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                    className="text-xs bg-slate-800 text-white px-4 py-2 rounded-xl font-medium hover:bg-slate-700 transition"
                  >
                    Change Photo
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      setPreview(null);
                    }}
                    className="text-xs bg-red-100 text-red-700 px-4 py-2 rounded-xl font-medium hover:bg-red-200 transition"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3 py-4">
                <div className="w-16 h-16 mx-auto bg-emerald-100 text-emerald-700 rounded-2xl flex items-center justify-center shadow-sm">
                  <Upload className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <p className="text-base font-semibold text-slate-800">
                    {t.dragDropText}
                  </p>
                  <p className="text-xs text-slate-500">
                    Supports JPG, PNG, WEBP (up to 8 MB)
                  </p>
                </div>

                <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                    className="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-sm transition active:scale-95"
                  >
                    <ImageIcon className="w-4 h-4" />
                    Browse Photos
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      cameraInputRef.current?.click();
                    }}
                    className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-sm transition active:scale-95"
                  >
                    <Camera className="w-4 h-4" />
                    {t.cameraButton}
                  </button>
                </div>
              </div>
            )}

            {/* Hidden native inputs */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => handleFileChange(e.target.files?.[0])}
              className="hidden"
            />
            <input
              type="file"
              ref={cameraInputRef}
              accept="image/jpeg,image/png,image/webp"
              capture="environment"
              onChange={(e) => handleFileChange(e.target.files?.[0])}
              className="hidden"
            />
          </div>

          {/* Photo Quality Tips Notice */}
          <div className="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-4 text-xs text-amber-900 space-y-1.5">
            <p className="font-bold flex items-center gap-1.5 text-amber-950">
              <Info className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>{t.photoTips}:</span>
            </p>
            <ul className="list-disc pl-5 space-y-1 text-[11px] text-amber-800">
              <li>Hold your camera steady; avoid motion blur.</li>
              <li>Ensure balanced daylight; avoid direct flash reflection or deep shadows.</li>
              <li>Make sure the affected leaf lesion fills at least 70% of the camera frame.</li>
            </ul>
          </div>

          {/* Optional Meta Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                {t.cropOptional}
              </label>
              <select
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium text-slate-800"
              >
                <option value="">-- Auto-detect from image --</option>
                {supportedCrops.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                {t.locationOptional}
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Field #3, North Plot"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              {t.notesOptional}
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Observed yellow spots after recent rain..."
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            disabled={loading || !file}
            className={`w-full py-4 px-6 rounded-2xl font-bold text-base shadow-lg transition flex items-center justify-center gap-2 ${
              loading
                ? "bg-slate-400 text-white cursor-wait"
                : !file
                ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                : "bg-emerald-700 hover:bg-emerald-800 text-white active:scale-[0.99]"
            }`}
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>{t.scanning}</span>
              </>
            ) : (
              <>
                <Sprout className="w-5 h-5" />
                <span>{t.scanButton}</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Recent Scans Section */}
      {recentReports.length > 0 && (
        <div className="mt-10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-slate-800">Recent Plant Scans</h3>
            <span className="text-xs text-slate-500">Your recent diagnostic history</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {recentReports.map((r) => (
              <div
                key={r.id}
                onClick={() => onSelectReport(r)}
                className="bg-white rounded-2xl border border-slate-200 p-3 hover:shadow-md transition cursor-pointer flex items-center gap-3"
              >
                <img
                  src={`/${r.image_path}`}
                  alt={r.crop}
                  className="w-14 h-14 object-cover rounded-xl border border-slate-100 flex-shrink-0"
                />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-slate-800 truncate">
                    {r.insight?.disease_name || r.predicted_class || "Diagnosed Leaf"}
                  </p>
                  <p className="text-[11px] text-slate-500 truncate">{r.crop || "Crop"}</p>
                  <span className={`inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    r.severity === "High" ? "bg-red-100 text-red-800" :
                    r.severity === "Medium" ? "bg-amber-100 text-amber-800" :
                    "bg-emerald-100 text-emerald-800"
                  }`}>
                    {r.severity ? `${r.severity} Severity` : "Healthy"}
                  </span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supported Crops Modal */}
      {showCropsModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-emerald-600" />
                <span>{t.supportedCrops}</span>
              </h3>
              <button
                onClick={() => setShowCropsModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg p-1"
              >
                ✕
              </button>
            </div>

            <div className="p-3 bg-amber-50 rounded-2xl border border-amber-200 text-amber-900 text-xs mb-4">
              <p className="font-semibold mb-1">⚠️ Crucial Model Limitation Note:</p>
              <p>{t.supportedCropsDisclaimer}</p>
            </div>

            <p className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wider">
              14 Supported Crop Families (38 Classes):
            </p>
            <div className="flex flex-wrap gap-2">
              {supportedCrops.map((c) => (
                <span
                  key={c}
                  className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium px-3 py-1.5 rounded-xl"
                >
                  🌱 {c}
                </span>
              ))}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={() => setShowCropsModal(false)}
                className="bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-4 py-2 rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
