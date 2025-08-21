import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, BarChart3, Database } from "lucide-react"

const reportSummary = {
  verdict: "supported",
  confidence: 0.89,
  keyMetrics: [
    { name: "BLEU Score", value: "29.2", improvement: "+2.4" },
    { name: "Training Time", value: "12.3h", improvement: "-6.4h" },
    { name: "Parameters", value: "65M", improvement: "+20M" },
  ],
  statistics: {
    pValue: "< 0.001",
    effectSize: "0.73",
    significance: "High",
  },
  reproducibility: {
    seed: "42",
    hash: "exp_20240115_143000",
    environment: "Python 3.9, PyTorch 1.12",
  },
}

export function ReportSummary() {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-foreground academic-text mb-4">Report Summary</h3>

      <div className="space-y-4">
        {/* Verdict */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium control-text">Verdict</span>
          </div>
          <div className="pl-6">
            <Badge className="bg-green-100 text-green-800 control-text">Hypothesis Supported</Badge>
            <div className="text-xs text-muted-foreground control-text mt-1">
              {Math.round(reportSummary.confidence * 100)}% confidence
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Key Results</span>
          </div>
          <div className="pl-6 space-y-2">
            {reportSummary.keyMetrics.map((metric, index) => (
              <div key={index} className="flex justify-between text-xs">
                <span className="text-muted-foreground control-text">{metric.name}:</span>
                <div className="text-right">
                  <span className="text-foreground academic-text">{metric.value}</span>
                  <span className="text-green-600 ml-1">({metric.improvement})</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Statistics */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Statistics</span>
          </div>
          <div className="pl-6 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">p-value:</span>
              <span className="text-foreground academic-text">{reportSummary.statistics.pValue}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Effect Size:</span>
              <span className="text-foreground academic-text">{reportSummary.statistics.effectSize}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Significance:</span>
              <Badge className="bg-green-100 text-green-800 text-xs control-text">
                {reportSummary.statistics.significance}
              </Badge>
            </div>
          </div>
        </div>

        {/* Reproducibility */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Reproducibility</span>
          </div>
          <div className="pl-6 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Seed:</span>
              <span className="font-mono text-foreground">{reportSummary.reproducibility.seed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Exp ID:</span>
              <span className="font-mono text-foreground text-xs">{reportSummary.reproducibility.hash}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
