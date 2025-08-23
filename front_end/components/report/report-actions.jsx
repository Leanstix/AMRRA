"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Download, FileJson, Mail, Link, Check } from "lucide-react"

export function ReportActions() {
  const [copied, setCopied] = useState(false)

  const handleDownloadPDF = () => {
    // Simulate PDF download
    console.log("Downloading PDF report...")
    // In real app: trigger PDF download
  }

  const handleExportJSON = () => {
    // Simulate JSON export
    const reportData = {
      id: "report_001",
      hypothesis: "Transformer architecture validation",
      verdict: "supported",
      confidence: 0.89,
      metrics: {
        bleu_score: 29.2,
        training_time: "12.3h",
        parameters: "65M",
      },
      statistics: {
        p_value: "<0.001",
        effect_size: 0.73,
        confidence_interval: "[28.8, 29.6]",
      },
    }

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "reproducibility_report.json"
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleShare = async () => {
    await navigator.clipboard.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleEmailShare = () => {
    const subject = "AI Research Reproducibility Report"
    const body = `I'd like to share this reproducibility report with you: ${window.location.href}`
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-foreground academic-text mb-4">Export & Share</h3>

      <div className="space-y-3">
        <Button onClick={handleDownloadPDF} className="w-full control-text">
          <Download className="h-4 w-4 mr-2" />
          Download PDF
        </Button>

        <Button variant="outline" onClick={handleExportJSON} className="w-full control-text bg-transparent">
          <FileJson className="h-4 w-4 mr-2" />
          Export JSON
        </Button>

        <div className="border-t border-border pt-3 space-y-2">
          <div className="text-sm font-medium text-foreground control-text mb-2">Share Report</div>

          <Button variant="outline" onClick={handleShare} className="w-full control-text bg-transparent">
            {copied ? <Check className="h-4 w-4 mr-2" /> : <Link className="h-4 w-4 mr-2" />}
            {copied ? "Link Copied!" : "Copy Link"}
          </Button>

          <Button variant="outline" onClick={handleEmailShare} className="w-full control-text bg-transparent">
            <Mail className="h-4 w-4 mr-2" />
            Share via Email
          </Button>
        </div>
      </div>

      <div className="mt-4 text-xs text-muted-foreground control-text">
        Reports are automatically archived and remain accessible for future reference.
      </div>
    </Card>
  )
}
