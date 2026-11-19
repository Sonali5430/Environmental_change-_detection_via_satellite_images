import React from "react"
import { Trophy, CheckCircle, BarChart3 } from "lucide-react"

export default function MetricsTable({ metricsTable, bestMethod }) {
  if (!metricsTable || metricsTable.length === 0) {
    return null
  }

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-700/80 overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-bold text-white">Algorithm Benchmark Performance</h3>
        </div>
        {bestMethod && (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-300">
            <Trophy className="w-3.5 h-3.5 text-amber-400" /> Best DIP: {bestMethod.replace("_", " ").toUpperCase()}
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider font-mono">
              <th className="py-3 px-4">Method</th>
              <th className="py-3 px-4">Precision</th>
              <th className="py-3 px-4">Recall</th>
              <th className="py-3 px-4">F1-Score</th>
              <th className="py-3 px-4">IoU (Jaccard)</th>
              <th className="py-3 px-4">Accuracy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {metricsTable.map((row) => {
              const isBest = row.method === bestMethod
              return (
                <tr
                  key={row.method}
                  className={`transition ${
                    isBest
                      ? "bg-amber-500/10 font-semibold text-amber-200"
                      : "hover:bg-slate-800/40 text-slate-300"
                  }`}
                >
                  <td className="py-3 px-4 font-sans font-medium flex items-center gap-2">
                    {isBest && <Trophy className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                    <span>{row.method.replace("_", " ").toUpperCase()}</span>
                  </td>
                  <td className="py-3 px-4">{(row.precision * 100).toFixed(2)}%</td>
                  <td className="py-3 px-4">{(row.recall * 100).toFixed(2)}%</td>
                  <td className="py-3 px-4 font-bold text-white">{(row.f1_score * 100).toFixed(2)}%</td>
                  <td className="py-3 px-4">{(row.iou * 100).toFixed(2)}%</td>
                  <td className="py-3 px-4">{(row.accuracy * 100).toFixed(2)}%</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
