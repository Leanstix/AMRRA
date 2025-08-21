"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Clock, CheckCircle } from "lucide-react"

export function ExperimentHeader({ experimentId }) {
  const experiment = {
    id: experimentId,
    hypothesis:
      "The Transformer architecture, relying entirely on self-attention mechanisms without recurrence or convolution, can achieve superior performance on machine translation tasks compared to existing sequence-to-sequence models.",
    paper: "Attention Is All You Need",
    startTime: "2024-01-15 14:30:00",
    endTime: "2024-01-16 02:45:00",
    duration: "12h 15m",
    status: "completed",
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => window.history.back()} className="control-text">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Plan
        </Button>
      </div>

      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-foreground academic-text">Experiment Results</h1>
              <p className="text-sm text-muted-foreground control-text">From: {experiment.paper}</p>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <Badge className="bg-green-100 text-green-800 control-text">Completed</Badge>
            </div>
          </div>

          <p className="text-foreground academic-text leading-relaxed">{experiment.hypothesis}</p>

          <div className="flex items-center gap-6 text-sm text-muted-foreground control-text">
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              <span>Duration: {experiment.duration}</span>
            </div>
            <div>Completed: {new Date(experiment.endTime).toLocaleString()}</div>
          </div>
        </div>
      </Card>
    </div>
  )
}
