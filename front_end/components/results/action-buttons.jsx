"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { FileText, Download, Share2, RefreshCw } from "lucide-react"

export function ActionButtons() {
  const handleGenerateReport = () => {
    window.location.href = "/report/1"
  }

  const handleDownloadData = () => {
    // Simulate download
    console.log("Downloading experiment data...")
  }

  const handleShare = () => {
    // Simulate sharing
    navigator.clipboard.writeText(window.location.href)
    console.log("Link copied to clipboard")
  }

  const handleRerun = () => {
    // Navigate back to experiment plan
    window.location.href = "/experiment-plan/1"
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-foreground academic-text mb-4">Actions</h3>

      <div className="space-y-3">
        <Button onClick={handleGenerateReport} className="w-full control-text">
          <FileText className="h-4 w-4 mr-2" />
          Generate Report
        </Button>

        <Button variant="outline" onClick={handleDownloadData} className="w-full control-text bg-transparent">
          <Download className="h-4 w-4 mr-2" />
          Download Data
        </Button>

        <Button variant="outline" onClick={handleShare} className="w-full control-text bg-transparent">
          <Share2 className="h-4 w-4 mr-2" />
          Share Results
        </Button>

        <Button variant="outline" onClick={handleRerun} className="w-full control-text bg-transparent">
          <RefreshCw className="h-4 w-4 mr-2" />
          Re-run Experiment
        </Button>
      </div>

      <div className="mt-4 text-xs text-muted-foreground control-text">
        All results are automatically saved and can be accessed later from your dashboard.
      </div>
    </Card>
  )
}
