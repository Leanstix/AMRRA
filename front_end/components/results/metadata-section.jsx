import { Card } from "@/components/ui/card"
import { Database, Hash, Cpu, Calendar } from "lucide-react"

const metadata = {
  datasetHash: "sha256:a1b2c3d4e5f6...",
  randomSeed: "42",
  gpuHours: "98.4",
  startTime: "2024-01-15 14:30:00",
  endTime: "2024-01-16 02:45:00",
  version: "v1.2.3",
  environment: "Python 3.9, PyTorch 1.12",
  reproductionHash: "exp_20240115_143000",
}

export function MetadataSection() {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-foreground academic-text mb-4">Experiment Metadata</h3>

      <div className="space-y-4">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Dataset</span>
          </div>
          <div className="pl-6 space-y-1">
            <div className="text-xs text-muted-foreground control-text">Hash:</div>
            <div className="text-xs font-mono text-foreground bg-muted/50 p-2 rounded">{metadata.datasetHash}</div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Hash className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Reproducibility</span>
          </div>
          <div className="pl-6 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Random Seed:</span>
              <span className="font-mono text-foreground">{metadata.randomSeed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Experiment ID:</span>
              <span className="font-mono text-foreground">{metadata.reproductionHash}</span>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Compute</span>
          </div>
          <div className="pl-6 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">GPU Hours:</span>
              <span className="text-foreground">{metadata.gpuHours}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Environment:</span>
              <span className="text-foreground">{metadata.environment}</span>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium control-text">Timeline</span>
          </div>
          <div className="pl-6 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Started:</span>
              <span className="text-foreground">{new Date(metadata.startTime).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground control-text">Completed:</span>
              <span className="text-foreground">{new Date(metadata.endTime).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
