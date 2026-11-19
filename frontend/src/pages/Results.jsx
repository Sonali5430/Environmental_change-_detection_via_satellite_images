import React, { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import {
  Download,
  BarChart3,
  Layers,
  MapPin,
  Flame,
  ArrowLeft,
  Percent,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Sparkles
} from "lucide-react"
import { api } from "../api/client"
import CompareSlider from "../components/CompareSlider"
import StatCard from "../components/StatCard"
import MapView from "../components/MapView"
import ChangeChart from "../components/ChangeChart"
import MetricsTable from "../components/MetricsTable"
import LoadingOverlay from "../components/LoadingOverlay"

export default function Results() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState("slider") // slider, overlay, mask, diff, map

  useEffect(() => {
    if (!id) return
    api.getAnalysisResults(id)
      .then((res) => {
        setData(res.data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [id])

  if (loading) return <LoadingOverlay />

  if (!data || data.status === "failed") {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Analysis Failed or Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">{data?.error || "Could not retrieve analytical record."}</p>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 text-white font-bold text-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Analyzer
        </Link>
      </div>
    )
  }

  const { stats, metrics, urls, use_case, method, is_multispectral } = data
  const baseUrl = "http://localhost:8000"

  const beforePreview = urls.before_preview ? `${baseUrl}${urls.before_preview}` : ""
  const afterPreview = urls.after_preview ? `${baseUrl}${urls.after_preview}` : ""
  const overlayUrl = urls.overlay ? `${baseUrl}${urls.overlay}` : ""
  const maskUrl = urls.change_mask ? `${baseUrl}${urls.change_mask}` : ""
  const diffUrl = urls.diff ? `${baseUrl}${urls.diff}` : ""
  const geojsonUrl = urls.geojson ? `${baseUrl}${urls.geojson}` : ""

  const tabs = [
    { id: "slider", label: "Before / After Slider", icon: Layers },
    { id: "overlay", label: "Change Overlay", icon: Flame },
    { id: "mask", label: "Binary Mask", icon: CheckCircle2 },
    { id: "diff", label: "Spectral Delta Map", icon: BarChart3 },
    { id: "map", label: "Leaflet GIS Map", icon: MapPin },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to="/history" className="hover:text-slate-200">History</Link>
            <span>/</span>
            <span className="font-mono text-slate-300">ID: {id}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Change Detection Report
            </h1>
            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              {use_case}
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/30">
              {method.replace("_", " ").toUpperCase()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to={`/compare/${id}`}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl glass-card text-slate-200 hover:text-white border border-slate-700 hover:border-slate-500 text-sm font-semibold transition"
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Benchmark Methods</span>
          </Link>

          {geojsonUrl && (
            <a
              href={geojsonUrl}
              download="change.geojson"
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-navy-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition"
            >
              <Download className="w-4 h-4" />
              <span>Export GeoJSON</span>
            </a>
          )}
        </div>
      </div>

      {/* Centerpiece Visualizations with Tabs */}
      <div className="space-y-4">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-xl glass-panel w-fit border border-slate-800">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                  isActive
                    ? "bg-emerald-500 text-navy-950 shadow-md"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Tab View Container */}
        <div className="min-h-[500px]">
          {activeTab === "slider" && (
            <CompareSlider beforeUrl={beforePreview} afterUrl={afterPreview} />
          )}

          {activeTab === "overlay" && overlayUrl && (
            <div className="rounded-2xl overflow-hidden glass-panel border border-slate-700/80 flex justify-center bg-navy-950 shadow-2xl p-2">
              <img src={overlayUrl} alt="Change Overlay" className="max-h-[600px] object-contain rounded-xl" />
            </div>
          )}

          {activeTab === "mask" && maskUrl && (
            <div className="rounded-2xl overflow-hidden glass-panel border border-slate-700/80 flex justify-center bg-navy-950 shadow-2xl p-2">
              <img src={maskUrl} alt="Binary Segmented Mask" className="max-h-[600px] object-contain rounded-xl" />
            </div>
          )}

          {activeTab === "diff" && diffUrl && (
            <div className="rounded-2xl overflow-hidden glass-panel border border-slate-700/80 flex justify-center bg-navy-950 shadow-2xl p-2">
              <img src={diffUrl} alt="Continuous Difference Map" className="max-h-[600px] object-contain rounded-xl" />
            </div>
          )}

          {activeTab === "map" && (
            <MapView geojsonUrl={geojsonUrl} fallbackImageUrl={overlayUrl} />
          )}
        </div>
      </div>

      {/* Quantitative Metric Stat Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            label="Changed Area"
            value={stats.changed_km2}
            unit="km²"
            color="#ef4444"
          />
          <StatCard
            label="Percent Change"
            value={stats.percent_change}
            unit="%"
            icon={Percent}
            color="#f59e0b"
          />
          <StatCard
            label="Gain Area"
            value={stats.gain_km2}
            unit="km²"
            color="#22c55e"
          />
          <StatCard
            label="Loss Area"
            value={stats.loss_km2}
            unit="km²"
            color="#ef4444"
          />
          <StatCard
            label="Change Regions"
            value={stats.num_regions}
            unit="patches"
            color="#06b6d4"
          />
        </div>
      )}

      {/* Analytics Grid: Recharts Gain vs Loss + Accuracy Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {stats && (
          <ChangeChart
            gainKm2={stats.gain_km2}
            lossKm2={stats.loss_km2}
            useCase={use_case}
          />
        )}

        {metrics ? (
          <div className="glass-panel rounded-2xl p-5 border border-slate-700/80">
            <h3 className="text-sm font-bold text-slate-200 mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Ground Truth Validation Metrics</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: "Precision", val: metrics.precision },
                { label: "Recall", val: metrics.recall },
                { label: "F1-Score", val: metrics.f1_score, highlight: true },
                { label: "IoU (Jaccard)", val: metrics.iou },
                { label: "Accuracy", val: metrics.accuracy },
              ].map((m, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border ${
                    m.highlight
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                      : "bg-navy-900/60 border-slate-800 text-slate-300"
                  }`}
                >
                  <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono mb-1">{m.label}</div>
                  <div className="text-xl font-bold font-mono">{(m.val * 100).toFixed(2)}%</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="glass-panel rounded-2xl p-5 border border-slate-700/80 flex flex-col justify-center text-center">
            <FileCode className="w-8 h-8 text-slate-500 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-300">Ground Truth Mask Not Provided</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Upload a binary ground truth mask during analysis to compute Precision, Recall, F1, and IoU automatically.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
