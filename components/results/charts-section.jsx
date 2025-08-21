"use client"

import { Card } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"

const trainingData = [
  { epoch: 1, bleu: 12.3, loss: 4.2 },
  { epoch: 5, bleu: 18.7, loss: 3.1 },
  { epoch: 10, bleu: 23.4, loss: 2.4 },
  { epoch: 15, bleu: 26.8, loss: 1.9 },
  { epoch: 20, bleu: 28.1, loss: 1.6 },
  { epoch: 25, bleu: 29.2, loss: 1.4 },
  { epoch: 30, bleu: 29.0, loss: 1.5 },
]

const comparisonData = [
  { model: "RNN Baseline", bleu: 26.8, params: 45 },
  { model: "Transformer", bleu: 29.2, params: 65 },
  { model: "Transformer + Attention", bleu: 30.1, params: 72 },
]

export function ChartsSection() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-foreground academic-text">Performance Analysis</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Training Progress */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-foreground academic-text mb-4">Training Progress</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trainingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="epoch" stroke="#374151" fontSize={12} fontFamily="DM Sans" />
                <YAxis stroke="#374151" fontSize={12} fontFamily="DM Sans" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e0e0e0",
                    borderRadius: "4px",
                    fontFamily: "DM Sans",
                  }}
                />
                <Line type="monotone" dataKey="bleu" stroke="#1e90ff" strokeWidth={2} name="BLEU Score" />
                <Line type="monotone" dataKey="loss" stroke="#ff6b6b" strokeWidth={2} name="Training Loss" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Model Comparison */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-foreground academic-text mb-4">Model Comparison</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="model" stroke="#374151" fontSize={12} fontFamily="DM Sans" />
                <YAxis stroke="#374151" fontSize={12} fontFamily="DM Sans" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#ffffff",
                    border: "1px solid #e0e0e0",
                    borderRadius: "4px",
                    fontFamily: "DM Sans",
                  }}
                />
                <Bar dataKey="bleu" fill="#1e90ff" name="BLEU Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  )
}
