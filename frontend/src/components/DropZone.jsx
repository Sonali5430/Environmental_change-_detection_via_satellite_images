import React, { useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { UploadCloud, CheckCircle2, X, FileSpreadsheet } from "lucide-react"

export default function DropZone({
  label,
  file,
  onFileSelect,
  onClear,
  acceptGeotiff = true,
  helperText = "GeoTIFF (.tif) or Plain Image (.png, .jpg)",
  accentColor = "#22c55e"
}) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles && acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0])
      }
    },
    [onFileSelect]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "image/tiff": [".tif", ".tiff"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
  })

  const isGeoTiff = file && (file.name.endsWith(".tif") || file.name.endsWith(".tiff"))

  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{label}</span>

      {file ? (
        <div
          style={{ borderColor: `${accentColor}40` }}
          className="relative glass-card rounded-2xl p-4 border flex items-center justify-between"
        >
          <div className="flex items-center gap-3 overflow-hidden">
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: `${accentColor}20`, color: accentColor }}
            >
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-white truncate">{file.name}</p>
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                <span>•</span>
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold"
                  style={{
                    backgroundColor: isGeoTiff ? "#06b6d420" : "#a855f720",
                    color: isGeoTiff ? "#06b6d4" : "#a855f7",
                  }}
                >
                  {isGeoTiff ? "GeoTIFF (Multi-band)" : "Standard RGB"}
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClear}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div
          {...getRootProps()}
          style={{
            borderColor: isDragActive ? accentColor : undefined,
            backgroundColor: isDragActive ? `${accentColor}08` : undefined,
          }}
          className={`cursor-pointer rounded-2xl p-6 border-2 border-dashed border-slate-700/80 hover:border-slate-500/80 transition-all text-center flex flex-col items-center justify-center gap-2 group glass-card`}
        >
          <input {...getInputProps()} />
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center mb-1 group-hover:scale-110 transition-transform"
            style={{ backgroundColor: `${accentColor}18`, color: accentColor }}
          >
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-slate-200">
            {isDragActive ? "Drop image file here" : "Drag & drop satellite image"}
          </p>
          <p className="text-xs text-slate-400">{helperText}</p>
        </div>
      )}
    </div>
  )
}
