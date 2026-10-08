import React, { useState } from "react";
import { 
  AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, Layers, 
  MessageSquare, ShieldAlert, Sparkles, ArrowLeft, RefreshCw, 
  HelpCircle, Eye, Info, FlaskConical, Sprout
} from "lucide-react";
import { translations } from "../translations";

export default function ResultView({ report, onBackToScan, onOpenChat, onAddExpertReview, currentUser, lang }) {
  const [showOverlay, setShowOverlay] = useState(true);
  const [openSections, setOpenSections] = useState({
    treatment: true,
    symptoms: false,
    causes: false,
    fertilizer: false,
    precautions: false,
    recovery: false
  });

  const [reviewVerdict, setReviewVerdict] = useState("agree");
  const [reviewComment, setReviewComment] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  const t = translations[lang] || translations.en;
  if (!report) return null;

  const toggleSection = (key) => {
    setOpenSections(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const isHealthy = report.predicted_class && report.predicted_class.toLowerCase().includes("healthy");
  const isNeedsBetterImage = report.status === "needs_better_image";
  const isLowConfidence = report.status === "low_confidence";
  const isLowCertainty = report.status === "completed_low_certainty";

  const insight = report.insight;
  const currentSeverity = report.severity || "Medium";
  const severityPlan = insight?.treatment_by_severity?.[currentSeverity] || insight?.treatment_by_severity?.Medium;

  const confidencePct = report.confidence ? Math.round(report.confidence * 100) : 0;
  const severityRatioPct = report.severity_ratio ? (report.severity_ratio * 100).toFixed(1) : "0.0";

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewComment.trim()) return;
    setSubmittingReview(true);
    try {
      await onAddExpertReview(report.id, reviewVerdict, reviewComment);
      setReviewComment("");
    } catch (err) {
      alert(err.message || "Failed to submit review");
    } finally {
      setSubmittingReview(false);
    }
  };

  // 1. STATE: NEEDS BETTER IMAGE
  if (isNeedsBetterImage) {
    const issue = report.validation_issue;
    return (
      <div className="max-w-2xl mx-auto px-4 py-10">
        <div className="bg-white rounded-3xl shadow-lg border border-amber-200 p-8 text-center">
          <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center text-amber-700 mx-auto mb-4">
            <AlertTriangle className="w-9 h-9" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800">
            {t.betterImageTitle}
          </h2>
          <p className="text-sm font-semibold text-amber-800 mt-2">
            {issue?.message || "The photo could not be reliably evaluated."}
          </p>

          {issue?.tips && (
            <div className="mt-6 bg-amber-50 rounded-2xl p-4 text-left border border-amber-200 text-xs text-amber-900 space-y-2">
              <p className="font-bold flex items-center gap-1.5">
                <Info className="w-4 h-4 text-amber-600" />
                <span>{t.photoTips}:</span>
              </p>
              <ul className="list-disc pl-5 space-y-1 text-amber-800">
                {issue.tips.map((tip, idx) => (
                  <li key={idx}>{tip}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-8 flex justify-center gap-4">
            <button
              onClick={onBackToScan}
              className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 px-6 rounded-2xl shadow transition flex items-center gap-2 text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Scan Again with Clearer Photo</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. STATE: COMPLETED OR LOW CONFIDENCE
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBackToScan}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-emerald-700 transition bg-white px-3.5 py-2 rounded-xl border border-slate-200 shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Crop Scanner</span>
        </button>

        <button
          onClick={() => onOpenChat(report)}
          className="flex items-center gap-2 text-xs font-bold bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2 rounded-xl shadow transition active:scale-95"
        >
          <MessageSquare className="w-4 h-4" />
          <span>{t.askBot}</span>
        </button>
      </div>

      {/* Main Diagnosis Header Card */}
      <div className="bg-white rounded-3xl shadow-md border border-slate-200 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 sm:p-8">
          {/* Image & Severity Overlay View */}
          <div className="space-y-3">
            <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-200 aspect-[4/3] flex items-center justify-center shadow-inner">
              <img
                src={showOverlay && report.overlay_path ? `/${report.overlay_path}` : `/${report.image_path}`}
                alt="Leaf scan"
                className="w-full h-full object-contain"
              />
              {/* Badge indicating view mode */}
              <div className="absolute top-3 left-3 bg-slate-900/80 backdrop-blur-md text-white text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-slate-700 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                <span>{showOverlay && report.overlay_path ? "OpenCV Severity Overlay" : "Original Leaf"}</span>
              </div>
            </div>

            {/* Toggle Overlay Button */}
            {report.overlay_path && (
              <div className="flex items-center justify-between px-1">
                <button
                  type="button"
                  onClick={() => setShowOverlay(!showOverlay)}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1.5 underline decoration-dotted"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Toggle {showOverlay ? "Original Photo" : "Severity Heatmap Overlay"}</span>
                </button>
                <span className="text-[10px] text-slate-400">
                  OpenCV HSV Heuristic Analysis
                </span>
              </div>
            )}
          </div>

          {/* Diagnosis & Metrics Column */}
          <div className="flex flex-col justify-between space-y-4">
            <div>
              {/* Crop & Category */}
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-0.5 rounded-full border border-emerald-200">
                  🌱 {report.crop || "Crop"}
                </span>
                <span className="bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-0.5 rounded-full capitalize">
                  {insight?.disease_type || "Diagnosis"}
                </span>
                {report.location && (
                  <span className="text-xs text-slate-400">
                    📍 {report.location}
                  </span>
                )}
              </div>

              {/* Disease Name */}
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {insight?.disease_name || report.predicted_class}
              </h1>
              {insight?.scientific_name && (
                <p className="text-xs italic text-slate-500 mt-0.5">
                  Scientific Name: {insight.scientific_name}
                </p>
              )}

              {/* Summary note */}
              <p className="text-xs text-slate-600 mt-3 leading-relaxed">
                {insight?.summary || (isHealthy ? "Your crop leaf shows no pathogenic damage." : "Leaf disease detected by local MobileNetV2.")}
              </p>
            </div>

            {/* Metrics: Severity & Confidence */}
            <div className="space-y-3 pt-2">
              {/* Severity Card */}
              {!isHealthy && report.severity && (
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5">
                  <div className="flex items-center justify-between text-xs font-bold mb-1.5">
                    <span className="text-slate-700 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span>{t.severity}: {report.severity}</span>
                    </span>
                    <span className={`px-2 py-0.5 rounded-md text-[11px] ${
                      report.severity === "High" ? "bg-red-100 text-red-800" :
                      report.severity === "Medium" ? "bg-amber-100 text-amber-800" :
                      "bg-emerald-100 text-emerald-800"
                    }`}>
                      {severityRatioPct}% Affected Area
                    </span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        report.severity === "High" ? "bg-red-500" :
                        report.severity === "Medium" ? "bg-amber-500" :
                        "bg-emerald-500"
                      }`}
                      style={{ width: `${Math.min(100, parseFloat(severityRatioPct) * 2)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Confidence Card */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5">
                <div className="flex items-center justify-between text-xs font-bold mb-1.5">
                  <span className="text-slate-700">{t.confidence}</span>
                  <span className={`px-2 py-0.5 rounded-md text-[11px] ${
                    confidencePct >= 85 ? "bg-emerald-100 text-emerald-800" :
                    confidencePct >= 60 ? "bg-amber-100 text-amber-800" :
                    "bg-red-100 text-red-800"
                  }`}>
                    {confidencePct}% Probability
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      confidencePct >= 85 ? "bg-emerald-500" :
                      confidencePct >= 60 ? "bg-amber-500" :
                      "bg-red-500"
                    }`}
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
              </div>

              {/* Status Warnings */}
              {isLowCertainty && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>{t.lowCertaintyNotice}</span>
                </div>
              )}

              {isLowConfidence && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 flex-shrink-0" />
                  <span>Confidence score is below 60%. Treatment plan withheld to avoid misapplication. Top alternatives are shown below.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Top-3 Differential Diagnoses */}
      {report.top3 && report.top3.length > 1 && (
        <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200">
          <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-emerald-600" />
            <span>{t.topAlternatives}</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {report.top3.map((alt, idx) => (
              <div key={idx} className="p-3 bg-slate-50 border border-slate-200/80 rounded-2xl">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold text-slate-800 truncate pr-2">
                    {alt.disease_name}
                  </span>
                  <span className="text-xs font-semibold text-emerald-700">
                    {Math.round(alt.probability * 100)}%
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 mb-2">{alt.crop}</p>
                <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-600 rounded-full"
                    style={{ width: `${Math.round(alt.probability * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collapsible IPM Insights Cards */}
      {insight && !isLowConfidence && (
        <div className="space-y-4">
          {/* 1. Treatment Action Plan (Open by default) */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => toggleSection("treatment")}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-emerald-100 text-emerald-700 rounded-xl flex items-center justify-center">
                  <Sprout className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">{t.treatment}</h3>
                  <p className="text-[11px] text-slate-500">Cultural, Organic & Approved Chemical Interventions</p>
                </div>
              </div>
              {openSections.treatment ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </button>

            {openSections.treatment && (
              <div className="p-5 pt-0 border-t border-slate-100 space-y-4 text-xs">
                {/* Immediate Cultural */}
                {severityPlan?.immediate_actions?.length > 0 && (
                  <div className="bg-emerald-50/60 border border-emerald-200/70 rounded-2xl p-4">
                    <p className="font-bold text-emerald-900 mb-2 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>{t.immediateActions} (IPM Phase 1):</span>
                    </p>
                    <ul className="list-disc pl-5 space-y-1 text-emerald-800">
                      {severityPlan.immediate_actions.map((act, i) => (
                        <li key={i}>{act}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Organic Options */}
                {severityPlan?.organic_options?.length > 0 && (
                  <div className="bg-teal-50/60 border border-teal-200/70 rounded-2xl p-4">
                    <p className="font-bold text-teal-900 mb-2 flex items-center gap-1.5">
                      <Sprout className="w-4 h-4 text-teal-600" />
                      <span>{t.organicOptions} (IPM Phase 2):</span>
                    </p>
                    <ul className="list-disc pl-5 space-y-1 text-teal-800">
                      {severityPlan.organic_options.map((org, i) => (
                        <li key={i}>{org}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Chemical Options */}
                {severityPlan?.chemical_options?.length > 0 && (
                  <div className="bg-amber-50/60 border border-amber-200/80 rounded-2xl p-4 space-y-3">
                    <p className="font-bold text-amber-950 flex items-center gap-1.5">
                      <FlaskConical className="w-4 h-4 text-amber-700" />
                      <span>{t.chemicalOptions} (Last Resort):</span>
                    </p>
                    {severityPlan.chemical_options.map((chem, i) => (
                      <div key={i} className="bg-white/90 p-3 rounded-xl border border-amber-200/60 space-y-1">
                        <p className="font-bold text-slate-800">
                          🧪 Active Ingredient: <span className="text-amber-900">{chem.active_ingredient}</span>
                        </p>
                        <p className="text-slate-600 text-[11px]">{chem.note}</p>
                        <p className="text-red-700 font-semibold text-[10px] mt-1">
                          ⚠️ Caution & PPE: {chem.caution}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 2. Symptoms */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => toggleSection("symptoms")}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-blue-100 text-blue-700 rounded-xl flex items-center justify-center">
                  <Info className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">{t.symptoms}</h3>
                  <p className="text-[11px] text-slate-500">Visual diagnosis markers on foliage and stem</p>
                </div>
              </div>
              {openSections.symptoms ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </button>
            {openSections.symptoms && (
              <div className="p-5 pt-0 border-t border-slate-100 text-xs text-slate-700">
                <ul className="list-disc pl-5 space-y-1.5">
                  {insight.symptoms?.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
          </div>

          {/* 3. Causes & Transmission */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => toggleSection("causes")}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-amber-100 text-amber-700 rounded-xl flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">{t.causes}</h3>
                  <p className="text-[11px] text-slate-500">Pathogen biology, humidity & vectors</p>
                </div>
              </div>
              {openSections.causes ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </button>
            {openSections.causes && (
              <div className="p-5 pt-0 border-t border-slate-100 text-xs text-slate-700">
                <ul className="list-disc pl-5 space-y-1.5">
                  {insight.causes_and_spread?.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}
          </div>

          {/* 4. Fertilizer & Nutrition */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => toggleSection("fertilizer")}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-lime-100 text-lime-800 rounded-xl flex items-center justify-center">
                  <Sprout className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">{t.fertilizer}</h3>
                  <p className="text-[11px] text-slate-500">Balanced N-P-K, calcium and micronutrients</p>
                </div>
              </div>
              {openSections.fertilizer ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </button>
            {openSections.fertilizer && (
              <div className="p-5 pt-0 border-t border-slate-100 text-xs text-slate-700">
                <ul className="list-disc pl-5 space-y-1.5">
                  {insight.fertilizer_and_nutrition?.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
            )}
          </div>

          {/* 5. Precautions & Prevention */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => toggleSection("precautions")}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-purple-100 text-purple-700 rounded-xl flex items-center justify-center">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">{t.precautions}</h3>
                  <p className="text-[11px] text-slate-500">Crop rotation, clean tools, and PPE safety</p>
                </div>
              </div>
              {openSections.precautions ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </button>
            {openSections.precautions && (
              <div className="p-5 pt-0 border-t border-slate-100 text-xs text-slate-700">
                <ul className="list-disc pl-5 space-y-1.5">
                  {insight.precautions_and_prevention?.map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>
            )}
          </div>

          {/* 6. Recovery Outlook */}
          <div className="bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden">
            <button
              type="button"
              onClick={() => toggleSection("recovery")}
              className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-50/50 transition"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">{t.recoveryOutlook}</h3>
                  <p className="text-[11px] text-slate-500">Expected timeline and when to seek extension help</p>
                </div>
              </div>
              {openSections.recovery ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
            </button>
            {openSections.recovery && (
              <div className="p-5 pt-0 border-t border-slate-100 text-xs text-slate-700 space-y-2">
                <p><strong>Timeline:</strong> {insight.recovery_outlook}</p>
                <p><strong>Extension Consultation:</strong> {insight.when_to_consult_expert}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Safety Disclaimer Banner */}
      <div className="p-4 bg-slate-100 rounded-2xl border border-slate-200 text-slate-600 text-[11px] flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
        <p>{t.disclaimer}</p>
      </div>

      {/* Expert Reviews Section */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-slate-200 space-y-4">
        <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span>{t.expertReviews}</span>
        </h3>

        {report.expert_reviews && report.expert_reviews.length > 0 ? (
          <div className="space-y-3">
            {report.expert_reviews.map((rev) => (
              <div key={rev.id} className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800">{rev.expert_name}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    rev.verdict === "agree" ? "bg-emerald-100 text-emerald-800" :
                    rev.verdict === "disagree" ? "bg-red-100 text-red-800" :
                    "bg-amber-100 text-amber-800"
                  }`}>
                    {rev.verdict === "agree" ? "Agreed with AI" : rev.verdict === "disagree" ? "Disagreed" : "Needs More Info"}
                  </span>
                </div>
                <p className="text-slate-600">{rev.comment}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic">No expert reviews submitted for this report yet.</p>
        )}

        {/* If current user is expert, provide review form */}
        {currentUser?.role === "expert" && (
          <form onSubmit={handleReviewSubmit} className="pt-4 border-t border-slate-100 space-y-3">
            <p className="text-xs font-bold text-slate-700">{t.addReview}:</p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setReviewVerdict("agree")}
                className={`py-2 px-3 rounded-xl text-xs font-medium border text-center transition ${
                  reviewVerdict === "agree" ? "bg-emerald-50 border-emerald-500 text-emerald-800 font-bold" : "border-slate-200 text-slate-600"
                }`}
              >
                Agree
              </button>
              <button
                type="button"
                onClick={() => setReviewVerdict("disagree")}
                className={`py-2 px-3 rounded-xl text-xs font-medium border text-center transition ${
                  reviewVerdict === "disagree" ? "bg-red-50 border-red-500 text-red-800 font-bold" : "border-slate-200 text-slate-600"
                }`}
              >
                Disagree
              </button>
              <button
                type="button"
                onClick={() => setReviewVerdict("needs_more_info")}
                className={`py-2 px-3 rounded-xl text-xs font-medium border text-center transition ${
                  reviewVerdict === "needs_more_info" ? "bg-amber-50 border-amber-500 text-amber-800 font-bold" : "border-slate-200 text-slate-600"
                }`}
              >
                Needs Info
              </button>
            </div>
            <textarea
              required
              rows={2}
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              placeholder="Enter agronomist observations and diagnosis verification..."
              className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={submittingReview}
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold py-2 px-4 rounded-xl text-xs shadow transition active:scale-95 disabled:opacity-50"
            >
              {submittingReview ? "Submitting..." : "Post Expert Review"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
