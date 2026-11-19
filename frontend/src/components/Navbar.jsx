import React, { useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { Globe, Layers, Activity, History as HistoryIcon, Satellite } from "lucide-react"
import { api } from "../api/client"

export default function Navbar() {
  const location = useLocation()
  const [online, setOnline] = useState(null)

  useEffect(() => {
    api.getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }, [])

  const navLinks = [
    { to: "/", label: "Home", icon: Globe },
    { to: "/analyze", label: "Analyze", icon: Layers },
    { to: "/history", label: "History", icon: HistoryIcon },
  ]

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 p-0.5 shadow-lg shadow-emerald-500/20 group-hover:shadow-emerald-500/40 transition">
            <div className="w-full h-full bg-navy-950 rounded-[10px] flex items-center justify-center">
              <Satellite className="w-5 h-5 text-emerald-400 group-hover:rotate-12 transition-transform duration-300" />
            </div>
          </div>
          <div>
            <div className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-emerald-400 bg-clip-text text-transparent">
              GeoChange DIP
            </div>
            <div className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">
              Satellite Change Detection
            </div>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {navLinks.map((link) => {
            const Icon = link.icon
            const isActive = location.pathname === link.to
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : "text-slate-300 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              online === true
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : online === false
                ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                online === true
                  ? "bg-emerald-400 animate-pulse"
                  : online === false
                  ? "bg-rose-400"
                  : "bg-slate-400"
              }`}
            />
            <span className="hidden sm:inline">
              {online === true ? "Backend Online" : online === false ? "Offline" : "Connecting"}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
