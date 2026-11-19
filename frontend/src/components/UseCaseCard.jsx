import React from "react"
import { Trees, Droplets, Flame, Building2, ArrowRight } from "lucide-react"

const iconMap = {
  deforestation: Trees,
  water: Droplets,
  burn_scars: Flame,
  urbanization: Building2,
}

export default function UseCaseCard({ useCase, isSelected, onSelect }) {
  const Icon = iconMap[useCase.id] || Trees

  return (
    <div
      onClick={() => onSelect && onSelect(useCase.id)}
      style={{
        borderColor: isSelected ? useCase.accent_color : undefined,
        boxShadow: isSelected ? `0 0 25px -5px ${useCase.accent_color}40` : undefined,
      }}
      className={`relative cursor-pointer rounded-2xl p-5 transition-all duration-300 glass-card border ${
        isSelected
          ? "bg-navy-900/90 scale-[1.02]"
          : "hover:border-slate-700 hover:-translate-y-1"
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg"
          style={{
            backgroundColor: `${useCase.accent_color}18`,
            color: useCase.accent_color,
            border: `1px solid ${useCase.accent_color}30`,
          }}
        >
          <Icon className="w-6 h-6" />
        </div>
        <span
          className="text-xs px-2.5 py-1 rounded-full font-mono font-semibold"
          style={{
            backgroundColor: `${useCase.accent_color}15`,
            color: useCase.accent_color,
            border: `1px solid ${useCase.accent_color}40`,
          }}
        >
          {useCase.index_name}
        </span>
      </div>

      <h3 className="text-lg font-bold text-white mb-1.5">{useCase.name}</h3>
      <p className="text-xs text-slate-400 leading-relaxed mb-4">{useCase.description}</p>

      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        <span className="text-slate-400 font-mono">{useCase.formula}</span>
        <span
          className="flex items-center gap-1 font-semibold"
          style={{ color: useCase.accent_color }}
        >
          Select <ArrowRight className="w-3.5 h-3.5" />
        </span>
      </div>
    </div>
  )
}
