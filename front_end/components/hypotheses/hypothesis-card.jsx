"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Play, FileText, Clock } from "lucide-react"

export function HypothesisCard({ hypothesis }) {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return "bg-green-100 text-green-800"
    if (confidence >= 0.7) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case "processing":
        return <Clock className="h-4 w-4" />
      case "completed":
        return <FileText className="h-4 w-4" />
      default:
        return <Play className="h-4 w-4" />
    }
  }

  const handleViewPlan = () => {
    window.location.href = `/experiment-plan/${hypothesis.id}`
  }

  const handleRunExperiment = () => {
    // Simulate starting experiment
    console.log(`Starting experiment for hypothesis ${hypothesis.id}`)
  }

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="space-y-4">
        {/* Header with confidence score */}
        <div className="flex items-start justify-between">
          <Badge className={`text-xs control-text ${getConfidenceColor(hypothesis.confidence)}`}>
            {Math.round(hypothesis.confidence * 100)}% confidence
          </Badge>
          <div className="flex items-center gap-1 text-muted-foreground">
            {getStatusIcon(hypothesis.status)}
            <span className="text-xs control-text capitalize">{hypothesis.status}</span>
          </div>
        </div>

        {/* Hypothesis text */}
        <div className="space-y-2">
          <p className="text-foreground academic-text leading-relaxed text-sm">{hypothesis.text}</p>
        </div>

        {/* Metrics and dataset info */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground control-text">
            <span className="font-medium">Dataset:</span> {hypothesis.dataset}
          </div>
          <div className="flex flex-wrap gap-1">
            {hypothesis.metrics.slice(0, 2).map((metric, index) => (
              <Badge key={index} variant="outline" className="text-xs control-text">
                {metric}
              </Badge>
            ))}
            {hypothesis.metrics.length > 2 && (
              <Badge variant="outline" className="text-xs control-text">
                +{hypothesis.metrics.length - 2} more
              </Badge>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" onClick={handleViewPlan} className="flex-1 control-text bg-transparent">
            <FileText className="h-4 w-4 mr-1" />
            View Plan
          </Button>
          <Button
            size="sm"
            onClick={handleRunExperiment}
            disabled={hypothesis.status === "processing"}
            className="flex-1 control-text"
          >
            <Play className="h-4 w-4 mr-1" />
            {hypothesis.status === "processing" ? "Running..." : "Run Experiment"}
          </Button>
        </div>
      </div>
    </Card>
  )
}
