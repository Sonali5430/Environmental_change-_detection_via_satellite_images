import React, { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Trophy, ArrowLeft, Layers, BarChart2 } from "lucide-react"
import { api } from "../api/client"
import MetricsTable from "../components/MetricsTable"
import LoadingOverlay from "../components/LoadingOverlay"

export default function Compare() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    api.compareMethods(id)
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

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl font-bold text-white mb-2">No Comparison Data Available</h2>
        <Link to={`/results/${id}`} className="text-emerald-400 text-sm font-semibold hover:underline">
          Return to Results
        </Link>
      </div>
    )
  }

  const { best_method, metrics_table, method_mask_urls, use_case } = data
  const baseUrl = "http://localhost:8000"

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link to={`/results/${id}`} className="hover:text-slate-200 flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Analysis
            </Link>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Algorithm Comparison Benchmark
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Side-by-side evaluation of all classical digital image processing change detection techniques.
          </p>
        </div>

        <div className="px-4 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-center gap-2 text-sm font-bold">
          <Trophy className="w-4 h-4 text-amber-400" />
          <span>Top Method: {best_method.replace("_", " ").toUpperCase()}</span>
        </div>
      </div>

      {/* Metrics Table */}
      {metrics_table && metrics_table.length > 0 && (
        <MetricsTable metricsTable={metrics_table} bestMethod={best_method} />
      )}

      {/* Side-by-side Method Output Mask Grid */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          <span>Generated Change Masks per Algorithm</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Object.entries(method_mask_urls).map(([methodName, maskUrl]) => {
            const isBest = methodName === best_method
            return (
              <div
                key={methodName}
                className={`glass-panel rounded-2xl p-4 border transition ${
                  isBest ? "border-amber-500/50 shadow-lg shadow-amber-500/10" : "border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    {methodName.replace("_", " ")}
                  </h3>
                  {isBest && (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      <Trophy className="w-3 h-3" /> Winner
                    </span>
                  )}
                </div>

                <div className="rounded-xl overflow-hidden bg-navy-950 border border-slate-800 aspect-square flex items-center justify-center">
                  <img
                    src={`${baseUrl}${maskUrl}`}
                    alt={`${methodName} Mask`}
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
