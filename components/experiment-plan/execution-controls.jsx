"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Play, Pause, Square, AlertCircle, CheckCircle, Clock } from "lucide-react"

export function ExecutionControls() {
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState("ready")

  const handleStart = () => {
    setIsRunning(true)
    setStatus("running")
    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsRunning(false)
          setStatus("completed")
          return 100
        }
        return prev + 2
      })
    }, 200)
  }

  const handlePause = () => {
    setIsRunning(false)
    setStatus("paused")
  }

  const handleStop = () => {
    setIsRunning(false)
    setProgress(0)
    setStatus("ready")
  }

  const getStatusIcon = () => {
    switch (status) {
      case "running":
        return <Clock className="h-4 w-4 text-blue-600" />
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return null
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case "running":
        return "bg-blue-100 text-blue-800"
      case "completed":
        return "bg-green-100 text-green-800"
      case "error":
        return "bg-red-100 text-red-800"
      case "paused":
        return "bg-yellow-100 text-yellow-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-xl font-semibold text-foreground academic-text mb-6">Execution Controls</h3>

      <div className="space-y-6">
        {/* Status */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium control-text">Status</span>
            <Badge className={`control-text ${getStatusColor()}`}>
              <div className="flex items-center gap-1">
                {getStatusIcon()}
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </div>
            </Badge>
          </div>

          {status === "running" && (
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground control-text">
                <span>Progress: {progress}%</span>
                <span>ETA: {Math.round((100 - progress) / 2)} min</span>
              </div>
            </div>
          )}
        </div>

        {/* Resource Requirements */}
        <div className="space-y-3">
          <h4 className="font-medium text-foreground academic-text">Resource Requirements</h4>
          <div className="bg-muted/50 p-3 rounded-lg space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="control-text">GPU:</span>
              <span className="academic-text">8x NVIDIA P100</span>
            </div>
            <div className="flex justify-between">
              <span className="control-text">Memory:</span>
              <span className="academic-text">64 GB RAM</span>
            </div>
            <div className="flex justify-between">
              <span className="control-text">Storage:</span>
              <span className="academic-text">100 GB</span>
            </div>
            <div className="flex justify-between">
              <span className="control-text">Duration:</span>
              <span className="academic-text">8-12 hours</span>
            </div>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="space-y-3">
          {status === "ready" && (
            <Button onClick={handleStart} className="w-full control-text">
              <Play className="h-4 w-4 mr-2" />
              Execute Experiment
            </Button>
          )}

          {status === "running" && (
            <div className="space-y-2">
              <Button variant="outline" onClick={handlePause} className="w-full control-text bg-transparent">
                <Pause className="h-4 w-4 mr-2" />
                Pause Experiment
              </Button>
              <Button variant="destructive" onClick={handleStop} className="w-full control-text">
                <Square className="h-4 w-4 mr-2" />
                Stop Experiment
              </Button>
            </div>
          )}

          {status === "paused" && (
            <div className="space-y-2">
              <Button onClick={handleStart} className="w-full control-text">
                <Play className="h-4 w-4 mr-2" />
                Resume Experiment
              </Button>
              <Button variant="destructive" onClick={handleStop} className="w-full control-text">
                <Square className="h-4 w-4 mr-2" />
                Stop Experiment
              </Button>
            </div>
          )}

          {status === "completed" && (
            <Button onClick={() => (window.location.href = "/results/1")} className="w-full control-text">
              <CheckCircle className="h-4 w-4 mr-2" />
              View Results
            </Button>
          )}
        </div>

        {/* Notifications */}
        <div className="text-xs text-muted-foreground control-text">
          You will receive email notifications when the experiment completes or encounters errors.
        </div>
      </div>
    </Card>
  )
}
