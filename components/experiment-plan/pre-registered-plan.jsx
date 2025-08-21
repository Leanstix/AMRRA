import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Database, Target, BarChart3, Clock } from "lucide-react"

const planDetails = {
  dataset: {
    name: "WMT 2014 English-German",
    size: "4.5M sentence pairs",
    split: "Train: 80%, Validation: 10%, Test: 10%",
    preprocessing: "BPE tokenization, vocabulary size: 37K",
  },
  metrics: [
    { name: "BLEU Score", threshold: "> 28.4", description: "Primary evaluation metric for translation quality" },
    { name: "Training Time", threshold: "< 12 hours", description: "Wall-clock time on 8 P100 GPUs" },
    { name: "Model Parameters", threshold: "< 65M", description: "Total trainable parameters" },
    { name: "Inference Speed", threshold: "> 100 tokens/sec", description: "Translation speed on single GPU" },
  ],
  hyperparameters: {
    "Learning Rate": "1e-4",
    "Batch Size": "25,000 tokens",
    "Warmup Steps": "4,000",
    Dropout: "0.1",
    "Label Smoothing": "0.1",
    Optimizer: "Adam (β1=0.9, β2=0.98, ε=1e-9)",
  },
  duration: "Estimated 8-12 hours",
}

export function PreRegisteredPlan() {
  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold text-foreground academic-text mb-6">Pre-Registered Experiment Plan</h2>

      <div className="space-y-6">
        {/* Dataset Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            <h3 className="font-medium text-foreground academic-text">Dataset Configuration</h3>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg space-y-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium control-text">Dataset:</span>
                <span className="ml-2 academic-text">{planDetails.dataset.name}</span>
              </div>
              <div>
                <span className="font-medium control-text">Size:</span>
                <span className="ml-2 academic-text">{planDetails.dataset.size}</span>
              </div>
              <div>
                <span className="font-medium control-text">Split:</span>
                <span className="ml-2 academic-text">{planDetails.dataset.split}</span>
              </div>
              <div>
                <span className="font-medium control-text">Preprocessing:</span>
                <span className="ml-2 academic-text">{planDetails.dataset.preprocessing}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <h3 className="font-medium text-foreground academic-text">Success Metrics & Thresholds</h3>
          </div>
          <div className="space-y-3">
            {planDetails.metrics.map((metric, index) => (
              <div key={index} className="bg-muted/50 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-foreground control-text">{metric.name}</span>
                  <Badge variant="outline" className="control-text">
                    {metric.threshold}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground academic-text">{metric.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Hyperparameters Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            <h3 className="font-medium text-foreground academic-text">Hyperparameters</h3>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              {Object.entries(planDetails.hyperparameters).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="font-medium control-text">{key}:</span>
                  <span className="academic-text">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Duration */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span className="control-text">{planDetails.duration}</span>
        </div>
      </div>
    </Card>
  )
}
