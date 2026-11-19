import React, { useEffect, useState } from "react"

export default function StatCard({ label, value, unit = "", icon: Icon, color = "#22c55e", delay = 0 }) {
  const [displayVal, setDisplayVal] = useState(0)

  useEffect(() => {
    if (typeof value !== "number") {
      setDisplayVal(value)
      return
    }

    let start = 0
    const end = value
    const duration = 1000
    const stepTime = 20
    const steps = duration / stepTime
    const increment = (end - start) / steps

    const timer = setInterval(() => {
      start += increment
      if ((increment > 0 && start >= end) || (increment < 0 && start <= end)) {
        setDisplayVal(end)
        clearInterval(timer)
      } else {
        setDisplayVal(Math.round(start * 100) / 100)
      }
    }, stepTime)

    return () => clearInterval(timer)
  }, [value])

  return (
    <div
      style={{ borderLeftColor: color }}
      className="glass-card rounded-xl p-4 sm:p-5 border-l-4 relative overflow-hidden"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        {Icon && (
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${color}18`, color }}
          >
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          {typeof displayVal === "number" ? displayVal.toLocaleString() : displayVal}
        </span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>
    </div>
  )
}
