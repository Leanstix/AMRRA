import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Clock, CheckCircle, XCircle } from "lucide-react"

const recentExperiments = [
  {
    id: 1,
    title: "Attention Is All You Need",
    status: "completed",
    hypotheses: 3,
    date: "2 hours ago",
    confidence: 0.87,
  },
  {
    id: 2,
    title: "BERT: Pre-training of Deep Bidirectional Transformers",
    status: "processing",
    hypotheses: 2,
    date: "1 day ago",
    confidence: 0.92,
  },
  {
    id: 3,
    title: "ResNet: Deep Residual Learning for Image Recognition",
    status: "completed",
    hypotheses: 4,
    date: "3 days ago",
    confidence: 0.78,
  },
  {
    id: 4,
    title: "GPT-3: Language Models are Few-Shot Learners",
    status: "failed",
    hypotheses: 1,
    date: "1 week ago",
    confidence: 0.65,
  },
]

const getStatusIcon = (status) => {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-4 w-4 text-green-600" />
    case "processing":
      return <Clock className="h-4 w-4 text-yellow-600" />
    case "failed":
      return <XCircle className="h-4 w-4 text-red-600" />
    default:
      return <FileText className="h-4 w-4 text-muted-foreground" />
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-800"
    case "processing":
      return "bg-yellow-100 text-yellow-800"
    case "failed":
      return "bg-red-100 text-red-800"
    default:
      return "bg-gray-100 text-gray-800"
  }
}

export function RecentExperiments() {
  return (
    <Card className="p-6">
      <h3 className="text-xl font-semibold text-foreground academic-text mb-6">Recent Experiments</h3>

      <div className="space-y-4">
        {recentExperiments.map((experiment) => (
          <Card key={experiment.id} className="p-4 hover:shadow-md transition-shadow">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  {getStatusIcon(experiment.status)}
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-foreground academic-text text-sm leading-tight">
                      {experiment.title}
                    </h4>
                    <p className="text-xs text-muted-foreground control-text mt-1">{experiment.date}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs control-text">
                    {experiment.hypotheses} hypotheses
                  </Badge>
                  <Badge className={`text-xs control-text ${getStatusColor(experiment.status)}`}>
                    {experiment.status}
                  </Badge>
                </div>

                {experiment.status === "completed" && (
                  <span className="text-xs text-muted-foreground control-text">
                    {Math.round(experiment.confidence * 100)}% confidence
                  </span>
                )}
              </div>

              {experiment.status === "completed" && (
                <Button variant="outline" size="sm" className="w-full text-xs control-text bg-transparent">
                  View Results
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>

      <Button variant="ghost" className="w-full mt-4 control-text">
        View All Experiments
      </Button>
    </Card>
  )
}
