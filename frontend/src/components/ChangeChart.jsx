import React from "react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"

export default function ChangeChart({ gainKm2 = 0, lossKm2 = 0, useCase = "deforestation" }) {
  const isUrban = useCase === "urbanization"

  const data = [
    {
      name: isUrban ? "Built-up Gain" : "Environmental Loss",
      area: isUrban ? gainKm2 : lossKm2,
      color: isUrban ? "#a855f7" : "#ef4444",
    },
    {
      name: isUrban ? "Reduction" : "Regrowth / Gain",
      area: isUrban ? lossKm2 : gainKm2,
      color: isUrban ? "#64748b" : "#22c55e",
    },
  ]

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-700/80 flex flex-col justify-between">
      <h3 className="text-sm font-bold text-slate-200 mb-2">Gain vs Loss Distribution (km²)</h3>
      <div className="w-full h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 40, bottom: 5 }}>
            <XAxis type="number" stroke="#94a3b8" fontSize={11} unit=" km²" />
            <YAxis type="category" dataKey="name" stroke="#cbd5e1" fontSize={12} width={110} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0b1329",
                borderColor: "#334155",
                borderRadius: "8px",
                color: "#f8fafc",
                fontSize: "12px",
              }}
            />
            <Bar dataKey="area" radius={[0, 6, 6, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
