import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

export function ReportsDashboard({ data, onHypothesisSelect }) {
  const { summary, hypotheses } = data;
  
  // Get the most recent hypotheses (top 5)
  const recentHypotheses = [...hypotheses]
    .sort((a, b) => {
      // Sort by status (running first, then completed, then failed)
      const statusOrder = { running: 0, completed: 1, failed: 2 };
      return statusOrder[a.status] - statusOrder[b.status];
    })
    .slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Summary Cards */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Hypotheses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.totalHypotheses}</div>
            <div className="flex mt-2 items-center text-xs text-muted-foreground">
              <div className="flex space-x-1">
                <Badge variant="outline" className="bg-green-100">{summary.completed} Completed</Badge>
                <Badge variant="outline" className="bg-blue-100">{summary.running} Running</Badge>
                <Badge variant="outline" className="bg-red-100">{summary.failed} Failed</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Completion Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round((summary.completed / summary.totalHypotheses) * 100)}%</div>
            <Progress 
              value={(summary.completed / summary.totalHypotheses) * 100} 
              className="mt-2" 
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average Effect Size</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.avgEffectSize.toFixed(2)}</div>
            <div className="text-xs text-muted-foreground mt-2">
              Across all completed experiments
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Verdict Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-2">
              <div className="text-green-600 font-bold">{summary.supported} Supported</div>
              <div className="text-red-600 font-bold">{summary.refuted} Refuted</div>
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              {summary.inconclusive} Inconclusive results
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Hypotheses */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Hypotheses</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Paper</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Verdict</TableHead>
                <TableHead>Effect Size</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentHypotheses.map((hypothesis) => (
                <TableRow 
                  key={hypothesis.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onHypothesisSelect(hypothesis)}
                >
                  <TableCell className="font-medium">{hypothesis.id}</TableCell>
                  <TableCell>{hypothesis.paper}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        hypothesis.status === "completed" ? "success" : 
                        hypothesis.status === "running" ? "default" : "destructive"
                      }
                    >
                      {hypothesis.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {hypothesis.verdict ? (
                      <Badge 
                        variant={hypothesis.verdict === "supported" ? "outline" : "secondary"}
                        className={
                          hypothesis.verdict === "supported" ? "bg-green-100" : 
                          hypothesis.verdict === "refuted" ? "bg-red-100" : "bg-gray-100"
                        }
                      >
                        {hypothesis.verdict}
                      </Badge>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell>
                    {hypothesis.metrics?.effectSize ? 
                      hypothesis.metrics.effectSize.toFixed(2) : "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}