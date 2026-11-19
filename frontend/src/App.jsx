import React from "react"
import { Routes, Route } from "react-router-dom"
import Navbar from "./components/Navbar"
import Home from "./pages/Home"
import Analyze from "./pages/Analyze"
import Results from "./pages/Results"
import Compare from "./pages/Compare"
import History from "./pages/History"

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-navy-950 text-slate-100">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/compare/:id" element={<Compare />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>GeoChange DIP — Environmental Satellite Change Detection • College Lab Mini Project</p>
      </footer>
    </div>
  )
}
