"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Target } from "lucide-react"

export function HypothesisOverview({ hypothesisId }) {
  // Mock data - in real app this would be fetched based on hypothesisId
  const hypothesis = {
    id: hypothesisId,
    text: "The Transformer architecture, relying entirely on self-attention mechanisms without recurrence or convolution, can achieve superior performance on machine translation tasks compared to existing sequence-to-sequence models.",
    confidence: 0.92,
    paper: "Attention Is All You Need",
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => window.history.back()} className="control-text">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Hypotheses
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-primary/10 rounded-lg">
            <Target className="h-6 w-6 text-primary" />
          </div>

          <div className="flex-1 space-y-3">
            <div className="flex items-start justify-between">
              <h1 className="text-2xl font-bold text-foreground academic-text">Experiment Plan</h1>
              <Badge className="bg-green-100 text-green-800 control-text">
                {Math.round(hypothesis.confidence * 100)}% confidence
              </Badge>
            </div>

            <p className="text-sm text-muted-foreground control-text">From: {hypothesis.paper}</p>

            <p className="text-foreground academic-text leading-relaxed">{hypothesis.text}</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
