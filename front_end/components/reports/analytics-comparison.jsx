import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Badge } from "../ui/badge";
import { Checkbox } from "../ui/checkbox";

export function AnalyticsComparison({ hypotheses }) {
  const [selectedHypotheses, setSelectedHypotheses] = useState([]);
  
  // Filter only completed hypotheses
  const completedHypotheses = hypotheses.filter(h => h.status === "completed");
  
  const handleHypothesisToggle = (hypothesisId) => {
    setSelectedHypotheses(prev => {
      if (prev.includes(hypothesisId)) {
        return prev.filter(id => id !== hypothesisId);
      } else {
        return [...prev, hypothesisId];
      }
    });
  };
  
  // Get the selected hypotheses data
  const selectedHypothesesData = completedHypotheses.filter(h => 
    selectedHypotheses.includes(h.id)
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Hypotheses Comparison</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h3 className="text-sm font-medium mb-2">Select Hypotheses to Compare</h3>
            <div className="space-y-2">
              {completedHypotheses.map((hypothesis) => (
                <div key={hypothesis.id} className="flex items-center space-x-2">
                  <Checkbox 
                    id={`hypothesis-${hypothesis.id}`}
                    checked={selectedHypotheses.includes(hypothesis.id)}
                    onCheckedChange={() => handleHypothesisToggle(hypothesis.id)}
                  />
                  <label 
                    htmlFor={`hypothesis-${hypothesis.id}`}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {hypothesis.id}: {hypothesis.paper} 
                    <span className="ml-2 text-muted-foreground">
                      ({hypothesis.verdict})
                    </span>
                  </label>
                </div>
              ))}
            </div>
          </div>
          
          {selectedHypothesesData.length > 0 ? (
            <>
              <div>
                <h3 className="text-sm font-medium mb-2">Comparison Table</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Metric</TableHead>
                      {selectedHypothesesData.map(h => (
                        <TableHead key={h.id}>{h.id}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">Effect Size</TableCell>
                      {selectedHypothesesData.map(h => (
                        <TableCell key={h.id}>
                          {h.metrics?.effectSize?.toFixed(2) || "N/A"}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">p-value</TableCell>
                      {selectedHypothesesData.map(h => (
                        <TableCell key={h.id}>
                          {h.metrics?.pValue?.toFixed(4) || "N/A"}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Accuracy</TableCell>
                      {selectedHypothesesData.map(h => (
                        <TableCell key={h.id}>
                          {h.metrics?.accuracy?.toFixed(2) || "N/A"}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">F1 Score</TableCell>
                      {selectedHypothesesData.map(h => (
                        <TableCell key={h.id}>
                          {h.metrics?.f1Score?.toFixed(2) || "N/A"}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">Verdict</TableCell>
                      {selectedHypothesesData.map(h => (
                        <TableCell key={h.id}>
                          {h.verdict ? (
                            <Badge 
                              variant={h.verdict === "supported" ? "outline" : "secondary"}
                              className={
                                h.verdict === "supported" ? "bg-green-100" : 
                                h.verdict === "refuted" ? "bg-red-100" : "bg-gray-100"
                              }
                            >
                              {h.verdict}
                            </Badge>
                          ) : (
                            "N/A"
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Comparison Visualization</h3>
                <div className="bg-muted h-64 rounded-md flex items-center justify-center">
                  <p className="text-muted-foreground">
                    Comparison chart would be displayed here
                  </p>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Summary Analysis</h3>
                <Card className="bg-muted/50">
                  <CardContent className="pt-6">
                    <p>
                      {selectedHypothesesData.length === 1 
                        ? "Select at least one more hypothesis to generate a comparison analysis."
                        : `Comparing ${selectedHypothesesData.length} hypotheses. The average effect size is ${
                            (selectedHypothesesData.reduce((sum, h) => sum + (h.metrics?.effectSize || 0), 0) / 
                            selectedHypothesesData.length).toFixed(2)
                          }. ${
                            selectedHypothesesData.filter(h => h.verdict === "supported").length
                          } hypotheses are supported and ${
                            selectedHypothesesData.filter(h => h.verdict === "refuted").length
                          } are refuted.`
                      }
                    </p>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <div className="bg-muted p-4 rounded-md text-center">
              <p className="text-muted-foreground">
                Select at least one hypothesis to view comparison
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}