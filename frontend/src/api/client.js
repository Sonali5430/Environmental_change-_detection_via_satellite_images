import axios from "axios"

const API_BASE = "http://localhost:8000/api"

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

export const api = {
  // Health & Catalog
  getHealth: () => apiClient.get("/health"),
  getUseCases: () => apiClient.get("/usecases"),

  // Analysis workflow
  analyzeImages: (formData, onProgress) =>
    apiClient.post("/analyze", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    }),

  getAnalysisStatus: (id) => apiClient.get(`/analyze/${id}/status`),
  getAnalysisResults: (id) => apiClient.get(`/results/${id}`),
  compareMethods: (id) => apiClient.get(`/compare/${id}`),

  // History
  getHistory: () => apiClient.get("/history"),
  deleteAnalysis: (id) => apiClient.delete(`/history/${id}`),
}

export default api
