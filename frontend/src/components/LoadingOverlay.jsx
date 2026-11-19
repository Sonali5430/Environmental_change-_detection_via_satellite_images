import React, { useEffect, useState } from "react"
import { Satellite, Loader2 } from "lucide-react"

const MESSAGES = [
  "Aligning multi-temporal coordinate grids...",
  "Running spatial denoising and radiometric normalization...",
  "Computing environmental spectral indices (NIR/SWIR)...",
  "Segmenting change vector magnitude...",
  "Applying morphological opening and region filtering...",
  "Computing quantitative ground statistics and GeoJSON...",
]

export default function LoadingOverlay({ status = "running" }) {
  const [msgIdx, setMsgIdx] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setMsgIdx((prev) => (prev + 1) % MESSAGES.length)
    }, 2200)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="fixed inset-0 z-50 bg-navy-950/80 backdrop-blur-xl flex flex-col items-center justify-center p-4">
      <div className="relative w-28 h-28 mb-8 flex items-center justify-center">
        {/* Animated radar rings */}
        <div className="absolute inset-0 rounded-full border-2 border-emerald-500/20 animate-ping" />
        <div className="absolute inset-2 rounded-full border border-cyan-500/40 animate-pulse" />
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-cyan-500 p-0.5 shadow-2xl shadow-emerald-500/30 flex items-center justify-center">
          <div className="w-full h-full bg-navy-950 rounded-[14px] flex items-center justify-center">
            <Satellite className="w-8 h-8 text-emerald-400 animate-bounce" />
          </div>
        </div>
      </div>

      <h3 className="text-xl font-bold text-white mb-2 tracking-tight">Processing Satellite Imagery</h3>
      <p className="text-sm text-slate-400 font-mono flex items-center gap-2 mb-6">
        <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
        <span>{MESSAGES[msgIdx]}</span>
      </p>

      <div className="w-64 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 animate-pulse rounded-full w-3/4" />
      </div>
    </div>
  )
}
