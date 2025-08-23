"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, FileText, Calendar, CheckCircle } from "lucide-react"

export function ReportHeader({ reportId }) {
  const report = {
    id: reportId,
    title: "Reproducibility Report: Attention Is All You Need",
    hypothesis:
      "The Transformer architecture, relying entirely on self-attention mechanisms without recurrence or convolution, can achieve superior performance on machine translation tasks compared to existing sequence-to-sequence models.",
    generatedAt: "2024-01-16 03:15:00",
    status: "completed",
    verdict: "supported",
    pages: 12,
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => window.history.back()} className="control-text">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Results
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-primary/10 rounded-lg">
            <FileText className="h-6 w-6 text-primary" />
          </div>

          <div className="flex-1 space-y-3">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <h1 className="text-2xl font-bold text-foreground academic-text">{report.title}</h1>
                <div className="flex items-center gap-4 text-sm text-muted-foreground control-text">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>Generated: {new Date(report.generatedAt).toLocaleString()}</span>
                  </div>
                  <div>{report.pages} pages</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <Badge className="bg-green-100 text-green-800 control-text">
                  {report.verdict === "supported" ? "Hypothesis Supported" : "Hypothesis Refuted"}
                </Badge>
              </div>
            </div>

            <p className="text-foreground academic-text leading-relaxed">{report.hypothesis}</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
