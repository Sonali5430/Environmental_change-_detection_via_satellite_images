import React, { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { ArrowRight, Satellite, ShieldCheck, Zap, Globe2, Sparkles } from "lucide-react"
import { api } from "../api/client"
import UseCaseCard from "../components/UseCaseCard"

export default function Home() {
  const [useCases, setUseCases] = useState([])

  useEffect(() => {
    api.getUseCases()
      .then((res) => setUseCases(res.data))
      .catch((err) => console.error(err))
  }, [])

  return (
    <div className="relative overflow-hidden min-h-[calc(100vh-4rem)]">
      {/* Background glow orb */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-gradient-to-tr from-emerald-500/10 via-cyan-500/10 to-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 relative z-10">
        {/* Hero Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Digital Image Processing For Earth Observation</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.15] mb-6"
          >
            Satellite Image Change Detection for{" "}
            <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-indigo-400 bg-clip-text text-transparent">
              Environmental Monitoring
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-base sm:text-lg text-slate-300 leading-relaxed mb-8"
          >
            Upload before and after satellite captures to detect canopy loss, reservoir shrinking,
            wildfire burn scars, and urban sprawl using classical digital image processing,
            spectral indexing, and geospatial morphology.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="flex flex-wrap items-center justify-center gap-4"
          >
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-base shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:scale-[1.02] active:scale-[0.98] transition"
            >
              <span>Start Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/history"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl glass-card text-slate-200 font-semibold text-base hover:text-white border hover:border-slate-600 transition"
            >
              <span>Past Analyses</span>
            </Link>
          </motion.div>
        </div>

        {/* Feature Pills */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20">
          {[
            { title: "Pure DIP Algorithms", desc: "No Black-Box Deep Learning", icon: Zap },
            { title: "Sentinel-2 Multi-Band", desc: "NIR, Red, Green & SWIR", icon: Satellite },
            { title: "RGB Fallback Engine", desc: "Works with Standard Imagery", icon: Globe2 },
            { title: "GIS & GeoJSON Export", desc: "Sub-pixel Area Statistics", icon: ShieldCheck },
          ].map((feat, idx) => {
            const Icon = feat.icon
            return (
              <div key={idx} className="glass-panel p-4 rounded-xl border border-slate-800/80 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">{feat.title}</h4>
                  <p className="text-xs text-slate-400">{feat.desc}</p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Use Cases Grid */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Environmental Use Cases</h2>
              <p className="text-sm text-slate-400 mt-1">Select an environmental application to get started</p>
            </div>
            <Link
              to="/analyze"
              className="hidden sm:flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300"
            >
              <span>Explore Analyzer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {useCases.map((uc) => (
              <Link key={uc.id} to={`/analyze?usecase=${uc.id}`}>
                <UseCaseCard useCase={uc} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
