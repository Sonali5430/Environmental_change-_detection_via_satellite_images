import React from "react"
import { ReactCompareSlider, ReactCompareSliderImage } from "react-compare-slider"

export default function CompareSlider({ beforeUrl, afterUrl, labelBefore = "Before Image", labelAfter = "After Image" }) {
  if (!beforeUrl || !afterUrl) {
    return (
      <div className="w-full aspect-video glass-panel rounded-2xl flex items-center justify-center text-slate-400 text-sm">
        No preview images available
      </div>
    )
  }

  return (
    <div className="relative rounded-2xl overflow-hidden glass-panel border border-slate-700/80 shadow-2xl">
      <ReactCompareSlider
        itemOne={<ReactCompareSliderImage src={beforeUrl} alt={labelBefore} />}
        itemTwo={<ReactCompareSliderImage src={afterUrl} alt={labelAfter} />}
        className="w-full max-h-[600px] object-contain"
      />
      <div className="absolute top-3 left-3 bg-navy-950/80 backdrop-blur-md px-3 py-1 rounded-lg text-xs font-semibold text-white border border-slate-700 pointer-events-none">
        {labelBefore}
      </div>
      <div className="absolute top-3 right-3 bg-navy-950/80 backdrop-blur-md px-3 py-1 rounded-lg text-xs font-semibold text-white border border-slate-700 pointer-events-none">
        {labelAfter}
      </div>
    </div>
  )
}
