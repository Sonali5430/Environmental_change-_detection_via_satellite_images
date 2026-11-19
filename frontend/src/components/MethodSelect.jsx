import React from "react"
import { Layers, Activity, Sparkles, Compass, Eye, AlertCircle } from "lucide-react"

const METHODS = [
  {
    id: "index_differencing",
    name: "Index Differencing",
    desc: "Direct physical thresholding on spectral index shifts (NDVI, NDWI, NBR, NDBI).",
    icon: Layers,
    requiresMulti: true,
  },
  {
    id: "image_differencing",
    name: "Image Differencing",
    desc: "Classical pixel-by-pixel grayscale intensity difference.",
    icon: Activity,
    requiresMulti: false,
  },
  {
    id: "pca",
    name: "PCA Differencing",
    desc: "Principal Component Analysis on stacked multi-spectral delta vectors.",
    icon: Sparkles,
    requiresMulti: false,
  },
  {
    id: "cva",
    name: "Change Vector Analysis (CVA)",
    desc: "Euclidean magnitude and spectral direction vector in n-dimensional space.",
    icon: Compass,
    requiresMulti: false,
  },
  {
    id: "ssim",
    name: "SSIM Dissimilarity",
    desc: "Structural Similarity Index metric (1 - SSIM) detecting pattern degradation.",
    icon: Eye,
    requiresMulti: false,
  },
]

export default function MethodSelect({ selectedMethod, onSelect, isRgbOnly, accentColor = "#22c55e" }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Change Detection Algorithm
        </span>
        {isRgbOnly && (
          <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
            <AlertCircle className="w-3.5 h-3.5" /> Plain RGB input: Spectral indices disabled
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {METHODS.map((m) => {
          const Icon = m.icon
          const disabled = isRgbOnly && m.requiresMulti
          const isSelected = selectedMethod === m.id

          return (
            <div
              key={m.id}
              onClick={() => !disabled && onSelect(m.id)}
              style={{
                borderColor: isSelected ? accentColor : undefined,
                boxShadow: isSelected ? `0 0 20px -5px ${accentColor}30` : undefined,
              }}
              className={`rounded-xl p-4 border transition-all text-left flex flex-col justify-between ${
                disabled
                  ? "opacity-40 cursor-not-allowed bg-slate-900/40 border-slate-800"
                  : isSelected
                  ? "bg-navy-900/90 cursor-pointer scale-[1.01]"
                  : "glass-card cursor-pointer hover:border-slate-600"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{
                      backgroundColor: isSelected ? `${accentColor}20` : "rgba(255,255,255,0.05)",
                      color: isSelected ? accentColor : "#94a3b8",
                    }}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  {m.requiresMulti && (
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      Multi-Band
                    </span>
                  )}
                </div>

                <h4 className="text-sm font-bold text-white mb-1">{m.name}</h4>
                <p className="text-xs text-slate-400 leading-relaxed">{m.desc}</p>
              </div>

              {disabled && (
                <div className="mt-2 text-[10px] text-amber-400/80 flex items-center gap-1 font-mono">
                  Requires 5-band GeoTIFF
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
