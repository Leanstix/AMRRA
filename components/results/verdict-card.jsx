import { Card } from "@/components/ui/card"
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react"

export function VerdictCard() {
  const result = {
    verdict: "supported", // "supported" | "refuted" | "inconclusive"
    confidence: 0.89,
    summary:
      "The experiment successfully demonstrates that the Transformer architecture achieves superior BLEU scores (29.2) compared to the baseline RNN model (26.8), with statistical significance (p < 0.001).",
  }

  const getVerdictDisplay = () => {
    switch (result.verdict) {
      case "supported":
        return {
          icon: <CheckCircle className="h-8 w-8 text-green-600" />,
          text: "Hypothesis Supported",
          bgColor: "bg-green-50",
          borderColor: "border-green-200",
          textColor: "text-green-800",
        }
      case "refuted":
        return {
          icon: <XCircle className="h-8 w-8 text-red-600" />,
          text: "Hypothesis Refuted",
          bgColor: "bg-red-50",
          borderColor: "border-red-200",
          textColor: "text-red-800",
        }
      default:
        return {
          icon: <AlertTriangle className="h-8 w-8 text-yellow-600" />,
          text: "Inconclusive Results",
          bgColor: "bg-yellow-50",
          borderColor: "border-yellow-200",
          textColor: "text-yellow-800",
        }
    }
  }

  const verdictDisplay = getVerdictDisplay()

  return (
    <Card className={`p-6 ${verdictDisplay.bgColor} ${verdictDisplay.borderColor} border-2`}>
      <div className="flex items-center gap-4">
        {verdictDisplay.icon}
        <div className="flex-1 space-y-2">
          <h2 className={`text-2xl font-bold ${verdictDisplay.textColor} academic-text`}>{verdictDisplay.text}</h2>
          <p className="text-sm text-muted-foreground control-text">
            Confidence: {Math.round(result.confidence * 100)}%
          </p>
          <p className="text-foreground academic-text leading-relaxed">{result.summary}</p>
        </div>
      </div>
    </Card>
  )
}
