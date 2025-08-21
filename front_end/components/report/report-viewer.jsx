"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ZoomIn, ZoomOut, RotateCw, Maximize2 } from "lucide-react"

export function ReportViewer() {
  const [zoom, setZoom] = useState(100)
  const [currentPage, setCurrentPage] = useState(1)
  const totalPages = 12

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200))
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50))

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Viewer Controls */}
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-foreground academic-text">Reproducibility Report</h2>

          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="control-text">
              Page {currentPage} of {totalPages}
            </Badge>
            <div className="flex items-center gap-1">
              <Button variant="outline" size="sm" onClick={handleZoomOut} className="control-text bg-transparent">
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-sm control-text px-2">{zoom}%</span>
              <Button variant="outline" size="sm" onClick={handleZoomIn} className="control-text bg-transparent">
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" className="control-text bg-transparent">
                <RotateCw className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" className="control-text bg-transparent">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Document Viewer */}
        <div className="border border-border rounded-lg overflow-hidden bg-gray-50">
          <div className="h-[800px] overflow-auto">
            <div
              className="bg-white mx-auto shadow-lg"
              style={{
                width: `${(8.5 * zoom) / 100}in`,
                minHeight: `${(11 * zoom) / 100}in`,
                transform: `scale(${zoom / 100})`,
                transformOrigin: "top center",
              }}
            >
              {/* Mock PDF Content */}
              <div className="p-8 space-y-6 academic-text">
                <div className="text-center space-y-4">
                  <h1 className="text-3xl font-bold text-foreground">AI Research Reproducibility Report</h1>
                  <h2 className="text-xl text-muted-foreground">
                    Attention Is All You Need: Transformer Architecture Validation
                  </h2>
                  <div className="text-sm text-muted-foreground">Generated on {new Date().toLocaleDateString()}</div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground">Executive Summary</h3>
                  <p className="leading-relaxed text-foreground">
                    This report presents the results of a comprehensive reproducibility study of the Transformer
                    architecture as described in "Attention Is All You Need" (Vaswani et al., 2017). The experiment
                    successfully validated the hypothesis that Transformer models achieve superior performance on
                    machine translation tasks compared to existing sequence-to-sequence models.
                  </p>

                  <h3 className="text-lg font-semibold text-foreground">Hypothesis</h3>
                  <div className="bg-blue-50 p-4 rounded border-l-4 border-blue-400">
                    <p className="leading-relaxed text-foreground">
                      The Transformer architecture, relying entirely on self-attention mechanisms without recurrence or
                      convolution, can achieve superior performance on machine translation tasks compared to existing
                      sequence-to-sequence models.
                    </p>
                  </div>

                  <h3 className="text-lg font-semibold text-foreground">Key Findings</h3>
                  <ul className="list-disc pl-6 space-y-2 text-foreground">
                    <li>BLEU score of 29.2 achieved, exceeding baseline RNN model (26.8) by 2.4 points</li>
                    <li>Training time reduced from 18.7 hours to 12.3 hours (34% improvement)</li>
                    <li>Statistical significance confirmed with p &lt; 0.001</li>
                    <li>Effect size of 0.73 indicates large practical significance</li>
                  </ul>

                  <h3 className="text-lg font-semibold text-foreground">Experimental Setup</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong>Dataset:</strong> WMT 2014 English-German
                    </div>
                    <div>
                      <strong>Model Parameters:</strong> 65M
                    </div>
                    <div>
                      <strong>Training Duration:</strong> 12.3 hours
                    </div>
                    <div>
                      <strong>Hardware:</strong> 8x NVIDIA P100
                    </div>
                  </div>

                  <h3 className="text-lg font-semibold text-foreground">Conclusion</h3>
                  <div className="bg-green-50 p-4 rounded border-l-4 border-green-400">
                    <p className="leading-relaxed text-foreground font-medium">
                      ✓ HYPOTHESIS SUPPORTED: The experimental results provide strong evidence supporting the hypothesis
                      with high statistical significance and practical importance.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page Navigation */}
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            className="control-text bg-transparent"
          >
            Previous
          </Button>
          <div className="flex items-center gap-2">
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => (
              <Button
                key={i + 1}
                variant={currentPage === i + 1 ? "default" : "outline"}
                size="sm"
                onClick={() => setCurrentPage(i + 1)}
                className="control-text"
              >
                {i + 1}
              </Button>
            ))}
            {totalPages > 5 && <span className="text-muted-foreground control-text">...</span>}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="control-text bg-transparent"
          >
            Next
          </Button>
        </div>
      </div>
    </Card>
  )
}
