import React, { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { History as HistoryIcon, Trash2, ArrowRight, ExternalLink, Calendar, MapPin } from "lucide-react"
import { api } from "../api/client"
import LoadingOverlay from "../components/LoadingOverlay"

export default function History() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchHistory = () => {
    api.getHistory()
      .then((res) => {
        setHistory(res.data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleDelete = async (id, e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!window.confirm("Are you sure you want to delete this analysis?")) return

    try {
      await api.deleteAnalysis(id)
      setHistory(history.filter((h) => h.id !== id))
    } catch (err) {
      alert("Failed to delete analysis.")
    }
  }

  if (loading) return <LoadingOverlay />

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <HistoryIcon className="w-7 h-7 text-emerald-400" />
            <span>Analysis History</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">Review past satellite change detection runs</p>
        </div>

        <Link
          to="/analyze"
          className="px-4 py-2 rounded-xl bg-emerald-500 text-navy-950 font-bold text-sm hover:bg-emerald-400 transition"
        >
          New Analysis
        </Link>
      </div>

      {history.length === 0 ? (
        <div className="glass-panel rounded-2xl p-16 text-center border border-slate-800">
          <HistoryIcon className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white mb-1">No Past Analyses Found</h3>
          <p className="text-xs text-slate-400 mb-5">Upload before and after scenes to run your first detection.</p>
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 text-navy-950 font-bold text-xs"
          >
            Launch Analyzer <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {history.map((item) => {
            const dateStr = new Date(item.created_at).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })
            const baseUrl = "http://localhost:8000"

            return (
              <div
                key={item.id}
                className="glass-card rounded-2xl overflow-hidden border border-slate-800 flex flex-col justify-between group"
              >
                <div>
                  {/* Thumbnail */}
                  <div className="aspect-video bg-navy-950 relative overflow-hidden border-b border-slate-800/80">
                    {item.overlay_url ? (
                      <img
                        src={`${baseUrl}${item.overlay_url}`}
                        alt="Change Overlay"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-xs text-slate-500 font-mono">
                        No Preview Available
                      </div>
                    )}
                    <div className="absolute top-2 left-2 px-2.5 py-1 rounded-md bg-navy-950/80 backdrop-blur-md text-[10px] font-bold uppercase tracking-wider text-emerald-400 border border-slate-700">
                      {item.use_case}
                    </div>
                  </div>

                  {/* Body */}
                  <div className="p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-slate-500" /> {dateStr}
                      </span>
                      <span className="text-cyan-400 font-semibold">{item.method.replace("_", " ")}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase font-mono block">Changed Area</span>
                        <span className="font-bold text-white text-sm">
                          {item.changed_km2 !== null ? `${item.changed_km2} km²` : "N/A"}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase font-mono block">Percent</span>
                        <span className="font-bold text-emerald-400 text-sm">
                          {item.percent_change !== null ? `${item.percent_change}%` : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer Actions */}
                <div className="p-3 bg-navy-900/60 border-t border-slate-800/80 flex items-center justify-between">
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                    title="Delete record"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <Link
                    to={`/results/${item.id}`}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-semibold border border-emerald-500/20 transition"
                  >
                    <span>View Analysis</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
