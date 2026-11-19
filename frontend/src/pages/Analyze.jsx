import React, { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { Layers, Play, Settings2, AlertTriangle } from "lucide-react"
import { api } from "../api/client"
import DropZone from "../components/DropZone"
import MethodSelect from "../components/MethodSelect"
import LoadingOverlay from "../components/LoadingOverlay"

export default function Analyze() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [useCases, setUseCases] = useState([])
  const [selectedUseCase, setSelectedUseCase] = useState(searchParams.get("usecase") || "deforestation")
  const [selectedMethod, setSelectedMethod] = useState("index_differencing")

  const [beforeFile, setBeforeFile] = useState(null)
  const [afterFile, setAfterFile] = useState(null)
  const [gtFile, setGtFile] = useState(null)

  // Advanced DIP Settings
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [thresholdMode, setThresholdMode] = useState("otsu")
  const [minArea, setMinArea] = useState(30)
  const [manualThresh, setManualThresh] = useState(0.25)

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false)
  const [uploadPercent, setUploadPercent] = useState(0)
  const [errorMsg, setErrorMsg] = useState("")

  useEffect(() => {
    api.getUseCases()
      .then((res) => setUseCases(res.data))
      .catch((err) => console.error(err))
  }, [])

  // Auto-detect plain RGB images
  const isRgbOnly =
    (beforeFile && !beforeFile.name.endsWith(".tif") && !beforeFile.name.endsWith(".tiff")) ||
    (afterFile && !afterFile.name.endsWith(".tif") && !afterFile.name.endsWith(".tiff"))

  useEffect(() => {
    if (isRgbOnly && selectedMethod === "index_differencing") {
      setSelectedMethod("image_differencing")
    }
  }, [isRgbOnly, selectedMethod])

  const currentUc = useCases.find((u) => u.id === selectedUseCase) || {
    id: "deforestation",
    name: "Deforestation",
    accent_color: "#22c55e",
  }

  const handleRunAnalysis = async (e) => {
    e.preventDefault()
    if (!beforeFile || !afterFile) {
      setErrorMsg("Please upload both Before and After satellite images.")
      return
    }

    setErrorMsg("")
    setIsProcessing(true)

    try {
      const formData = new FormData()
      formData.append("before", beforeFile)
      formData.append("after", afterFile)
      if (gtFile) formData.append("ground_truth", gtFile)
      formData.append("use_case", selectedUseCase)
      formData.append("method", selectedMethod)
      formData.append("min_area", minArea.toString())
      formData.append("threshold_mode", thresholdMode)
      if (thresholdMode === "manual") {
        formData.append("threshold_val", manualThresh.toString())
      }

      const res = await api.analyzeImages(formData, (pct) => setUploadPercent(pct))
      const analysisId = res.data.id

      // Poll status until done
      const pollTimer = setInterval(async () => {
        try {
          const statusRes = await api.getAnalysisStatus(analysisId)
          if (statusRes.data.status === "done") {
            clearInterval(pollTimer)
            setIsProcessing(false)
            navigate(`/results/${analysisId}`)
          } else if (statusRes.data.status === "failed") {
            clearInterval(pollTimer)
            setIsProcessing(false)
            setErrorMsg(statusRes.data.error || "Analysis pipeline failed.")
          }
        } catch (err) {
          clearInterval(pollTimer)
          setIsProcessing(false)
          setErrorMsg("Failed to poll analysis progress.")
        }
      }, 1500)
    } catch (err) {
      setIsProcessing(false)
      setErrorMsg(err.response?.data?.detail || "Failed to start analysis.")
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative">
      {isProcessing && <LoadingOverlay />}

      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Run Change Detection</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure environmental use case, upload multi-temporal imagery, and run classical DIP analysis.
        </p>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleRunAnalysis} className="space-y-8">
        {/* 1. Use Case Selector */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-4">
            1. Select Environmental Use Case
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {useCases.map((uc) => (
              <button
                type="button"
                key={uc.id}
                onClick={() => setSelectedUseCase(uc.id)}
                style={{
                  borderColor: selectedUseCase === uc.id ? uc.accent_color : undefined,
                  backgroundColor: selectedUseCase === uc.id ? `${uc.accent_color}15` : undefined,
                }}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  selectedUseCase === uc.id
                    ? "font-bold text-white shadow-lg"
                    : "border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <div className="text-sm font-bold">{uc.name}</div>
                <div className="text-xs font-mono mt-0.5 opacity-80">{uc.index_name}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 2. Drag & Drop Imagery */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-4">
            2. Upload Satellite Imagery
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
            <DropZone
              label="Before Satellite Image"
              file={beforeFile}
              onFileSelect={setBeforeFile}
              onClear={() => setBeforeFile(null)}
              accentColor={currentUc.accent_color}
            />
            <DropZone
              label="After Satellite Image"
              file={afterFile}
              onFileSelect={setAfterFile}
              onClear={() => setAfterFile(null)}
              accentColor={currentUc.accent_color}
            />
          </div>

          <div className="pt-4 border-t border-slate-800/80">
            <DropZone
              label="Optional Ground Truth Change Mask"
              file={gtFile}
              onFileSelect={setGtFile}
              onClear={() => setGtFile(null)}
              helperText="Binary mask (.png, .tif) for automatic accuracy & F1-score evaluation"
              accentColor="#f59e0b"
            />
          </div>
        </div>

        {/* 3. Method Selection */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-4">
            3. Choose Detection Method
          </span>
          <MethodSelect
            selectedMethod={selectedMethod}
            onSelect={setSelectedMethod}
            isRgbOnly={isRgbOnly}
            accentColor={currentUc.accent_color}
          />
        </div>

        {/* 4. Advanced Settings Toggle */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full text-left"
          >
            <div className="flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-300">Advanced DIP Filtering & Thresholding</span>
            </div>
            <span className="text-xs text-emerald-400 font-mono font-medium">
              {showAdvanced ? "Hide Options" : "Show Options"}
            </span>
          </button>

          {showAdvanced && (
            <div className="mt-6 pt-6 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
                  Threshold Mode
                </label>
                <select
                  value={thresholdMode}
                  onChange={(e) => setThresholdMode(e.target.value)}
                  className="w-full bg-navy-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="otsu">Otsu Automatic Binarization</option>
                  <option value="adaptive">Adaptive Gaussian Thresholding</option>
                  <option value="manual">Manual Cutoff Value</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
                  Min Region Size: {minArea} pixels
                </label>
                <input
                  type="range"
                  min="5"
                  max="150"
                  step="5"
                  value={minArea}
                  onChange={(e) => setMinArea(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
                <span className="text-[11px] text-slate-400">Filters out isolated speckle noise smaller than {minArea} pixels</span>
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          style={{
            backgroundColor: currentUc.accent_color,
            boxShadow: `0 10px 25px -5px ${currentUc.accent_color}50`,
          }}
          className="w-full py-4 rounded-xl text-navy-950 font-extrabold text-base flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.99] transition cursor-pointer"
        >
          <Play className="w-5 h-5 fill-current" />
          <span>Execute Change Detection Pipeline</span>
        </button>
      </form>
    </div>
  )
}
