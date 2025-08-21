import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const statistics = [
  {
    metric: "BLEU Score",
    value: "29.2",
    baseline: "26.8",
    improvement: "+2.4",
    pValue: "< 0.001",
    effectSize: "0.73",
    confidenceInterval: "[28.8, 29.6]",
    significance: "high",
  },
  {
    metric: "Training Time",
    value: "12.3h",
    baseline: "18.7h",
    improvement: "-6.4h",
    pValue: "< 0.01",
    effectSize: "1.12",
    confidenceInterval: "[11.8, 12.8]",
    significance: "high",
  },
  {
    metric: "Model Parameters",
    value: "65M",
    baseline: "45M",
    improvement: "+20M",
    pValue: "N/A",
    effectSize: "N/A",
    confidenceInterval: "N/A",
    significance: "none",
  },
  {
    metric: "Inference Speed",
    value: "127 tok/s",
    baseline: "89 tok/s",
    improvement: "+38 tok/s",
    pValue: "< 0.05",
    effectSize: "0.45",
    confidenceInterval: "[119, 135]",
    significance: "medium",
  },
]

export function StatisticsTable() {
  const getSignificanceBadge = (significance) => {
    switch (significance) {
      case "high":
        return <Badge className="bg-green-100 text-green-800 control-text">High</Badge>
      case "medium":
        return <Badge className="bg-yellow-100 text-yellow-800 control-text">Medium</Badge>
      case "low":
        return <Badge className="bg-red-100 text-red-800 control-text">Low</Badge>
      default:
        return (
          <Badge variant="secondary" className="control-text">
            N/A
          </Badge>
        )
    }
  }

  const getImprovementColor = (improvement) => {
    if (improvement.startsWith("+") && !improvement.includes("Parameters")) {
      return "text-green-600"
    } else if (improvement.startsWith("-")) {
      return "text-green-600"
    }
    return "text-muted-foreground"
  }

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-foreground academic-text mb-6">Statistical Analysis</h2>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">Metric</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">Value</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">Baseline</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">Improvement</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">p-value</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">Effect Size</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">95% CI</th>
              <th className="text-left py-3 px-2 font-medium text-foreground control-text">Significance</th>
            </tr>
          </thead>
          <tbody>
            {statistics.map((stat, index) => (
              <tr key={index} className="border-b border-border/50">
                <td className="py-3 px-2 font-medium text-foreground academic-text">{stat.metric}</td>
                <td className="py-3 px-2 text-foreground academic-text">{stat.value}</td>
                <td className="py-3 px-2 text-muted-foreground academic-text">{stat.baseline}</td>
                <td className={`py-3 px-2 font-medium academic-text ${getImprovementColor(stat.improvement)}`}>
                  {stat.improvement}
                </td>
                <td className="py-3 px-2 text-foreground academic-text">{stat.pValue}</td>
                <td className="py-3 px-2 text-foreground academic-text">{stat.effectSize}</td>
                <td className="py-3 px-2 text-foreground academic-text">{stat.confidenceInterval}</td>
                <td className="py-3 px-2">{getSignificanceBadge(stat.significance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-sm text-muted-foreground academic-text">
        Statistical significance determined using two-tailed t-test with α = 0.05. Effect sizes calculated using Cohen's
        d.
      </div>
    </Card>
  )
}
