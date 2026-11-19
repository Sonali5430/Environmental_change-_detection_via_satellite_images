import React, { useEffect, useState } from "react"
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet"
import { MapPin, AlertCircle } from "lucide-react"

export default function MapView({ geojsonUrl, fallbackImageUrl, accentColor = "#ef4444" }) {
  const [geoData, setGeoData] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!geojsonUrl) return

    fetch(geojsonUrl)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch GeoJSON")
        return res.json()
      })
      .then((data) => {
        if (data && data.features && data.features.length > 0) {
          // Check if coordinates look geographic (lon between -180 and 180, lat between -90 and 90)
          const firstCoord = data.features[0].geometry.coordinates[0][0]
          if (Math.abs(firstCoord[0]) <= 180 && Math.abs(firstCoord[1]) <= 90) {
            setGeoData(data)
          } else {
            setError(true)
          }
        } else {
          setError(true)
        }
      })
      .catch(() => setError(true))
  }, [geojsonUrl])

  if (error || !geoData) {
    return (
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Image data is pixel-aligned (non-projected). Displaying high-resolution overlay preview:</span>
        </div>
        {fallbackImageUrl && (
          <div className="rounded-2xl overflow-hidden glass-panel border border-slate-700 flex justify-center bg-navy-950">
            <img src={fallbackImageUrl} alt="Change Map Overlay" className="max-h-[550px] object-contain" />
          </div>
        )}
      </div>
    )
  }

  // Calculate rough center from first polygon
  const centerCoord = geoData.features[0].geometry.coordinates[0][0]
  const center = [centerCoord[1], centerCoord[0]]

  const styleGeoJson = () => ({
    color: accentColor,
    weight: 2,
    opacity: 0.9,
    fillColor: accentColor,
    fillOpacity: 0.45,
  })

  return (
    <div className="rounded-2xl overflow-hidden glass-panel border border-slate-700/80 h-[550px] relative shadow-2xl">
      <MapContainer center={center} zoom={13} scrollWheelZoom={false} className="w-full h-full">
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <GeoJSON data={geoData} style={styleGeoJson} />
      </MapContainer>
      <div className="absolute bottom-3 left-3 z-[1000] bg-navy-950/85 backdrop-blur-md px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 border border-slate-700 flex items-center gap-2">
        <MapPin className="w-3.5 h-3.5 text-emerald-400" />
        <span>Leaflet GIS • {geoData.features.length} GeoJSON Change Polygons (WGS84 EPSG:4326)</span>
      </div>
    </div>
  )
}
