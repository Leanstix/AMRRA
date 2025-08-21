"use client"

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"

const SETTINGS_STORAGE_KEY = "mlra_settings_v1"

const defaultSettings = {
  experiment: {
    randomSeed: 42,
    numRuns: 3,
    confidenceLevel: 0.95,
    metrics: ["Accuracy", "F1"],
    sandboxMode: true,
  },
  data: {
    source: "upload", // upload | synthetic
    hashingEnabled: true,
    preprocessing: {
      normalize: true,
      tokenize: true,
      lowercase: true,
      removeStopwords: false,
    },
  },
  paper: {
    inputFormat: "pdf", // pdf | arxiv | text
    claimSensitivity: 0.6,
    hypothesis: {
      threshold: 0.5,
      minEffectSize: 0.2,
      nullAssumption: "two_tailed",
    },
  },
  execution: {
    cpuLimit: 4,
    gpuLimit: 1,
    timeoutMinutes: 60,
    parallelRuns: 2,
    loggingLevel: "info", // error | warn | info | debug
  },
  reporting: {
    format: "html", // html | pdf
    includeCode: false,
    includePlots: true,
    artifactDir: "./artifacts",
  },
  notifications: {
    onCompletion: true,
    onErrors: true,
  },
  advanced: {
    agentTimeoutSeconds: 120,
    customAgentPrompt: "",
    vectorStore: {
      provider: "faiss",
      indexPath: "./vector_index",
    },
  },
}

const SettingsContext = createContext({
  settings: defaultSettings,
  updateSettings: (_updater) => {},
  resetSettings: () => {},
})

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(defaultSettings)

  // load
  useEffect(() => {
    try {
      const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        setSettings({ ...defaultSettings, ...parsed })
      }
    } catch (_) {
      // ignore
    }
  }, [])

  // persist
  useEffect(() => {
    try {
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
    } catch (_) {
      // ignore
    }
  }, [settings])

  const updateSettings = useCallback((updater) => {
    setSettings((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater
      return next
    })
  }, [])

  const resetSettings = useCallback(() => setSettings(defaultSettings), [])

  const value = useMemo(() => ({ settings, updateSettings, resetSettings }), [settings, updateSettings, resetSettings])

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  return useContext(SettingsContext)
}

export function getDefaultSettings() {
  return defaultSettings
}


