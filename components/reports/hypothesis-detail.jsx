import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Badge } from "../ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../ui/accordion";

export function HypothesisDetail({ hypothesis }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{hypothesis.id}: {hypothesis.paper}</CardTitle>
              <p className="text-muted-foreground mt-1">{hypothesis.claim}</p>
            </div>
            <div className="flex space-x-2">
              <Badge 
                variant={
                  hypothesis.status === "completed" ? "success" : 
                  hypothesis.status === "running" ? "default" : "destructive"
                }
                className="text-sm"
              >
                {hypothesis.status}
              </Badge>
              {hypothesis.verdict && (
                <Badge 
                  variant={hypothesis.verdict === "supported" ? "outline" : "secondary"}
                  className={
                    hypothesis.verdict === "supported" ? "bg-green-100" : 
                    hypothesis.verdict === "refuted" ? "bg-red-100" : "bg-gray-100"
                  }
                >
                  {hypothesis.verdict}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="plan">
            <TabsList className="grid grid-cols-3 mb-4">
              <TabsTrigger value="plan">Experiment Plan</TabsTrigger>
              <TabsTrigger value="code">Code</TabsTrigger>
              <TabsTrigger value="metrics">Metrics & Plots</TabsTrigger>
            </TabsList>
            
            <TabsContent value="plan" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Preregistered Experiment Plan</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium">Method</h3>
                      <p>{hypothesis.preregisteredPlan.method}</p>
                    </div>
                    <div>
                      <h3 className="font-medium">Dataset</h3>
                      <p>{hypothesis.preregisteredPlan.dataset}</p>
                    </div>
                    <div>
                      <h3 className="font-medium">Parameters</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Parameter</TableHead>
                            <TableHead>Value</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {Object.entries(hypothesis.preregisteredPlan.parameters).map(([key, value]) => (
                            <TableRow key={key}>
                              <TableCell>{key}</TableCell>
                              <TableCell>{typeof value === 'object' ? JSON.stringify(value) : value.toString()}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="code">
              <Card>
                <CardHeader>
                  <CardTitle>Experiment Code</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded-md overflow-auto text-sm">
                    <code>{hypothesis.code || "No code available"}</code>
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="metrics" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Execution Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  {hypothesis.metrics ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Effect Size</p>
                        <p className="text-2xl font-bold">{hypothesis.metrics.effectSize?.toFixed(2) || "N/A"}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">p-value</p>
                        <p className="text-2xl font-bold">{hypothesis.metrics.pValue?.toFixed(4) || "N/A"}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Confidence Interval</p>
                        <p className="text-2xl font-bold">
                          {hypothesis.metrics.confidenceInterval ? 
                            `[${hypothesis.metrics.confidenceInterval[0].toFixed(2)}, ${hypothesis.metrics.confidenceInterval[1].toFixed(2)}]` : 
                            "N/A"}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Accuracy</p>
                        <p className="text-2xl font-bold">{hypothesis.metrics.accuracy?.toFixed(2) || "N/A"}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">F1 Score</p>
                        <p className="text-2xl font-bold">{hypothesis.metrics.f1Score?.toFixed(2) || "N/A"}</p>
                      </div>
                    </div>
                  ) : (
                    <p>No metrics available</p>
                  )}
                </CardContent>
              </Card>
              
              {hypothesis.plots && hypothesis.plots.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Plots & Visualizations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible className="w-full">
                      {hypothesis.plots.map((plot, index) => (
                        <AccordionItem key={index} value={`plot-${index}`}>
                          <AccordionTrigger>{plot.title}</AccordionTrigger>
                          <AccordionContent>
                            <div className="bg-muted p-4 rounded-md">
                              {/* Placeholder for actual chart visualization */}
                              <div className="h-64 flex items-center justify-center border border-dashed border-muted-foreground rounded-md">
                                <p className="text-muted-foreground">
                                  {plot.type === "bar" ? "Bar Chart" : "Line Chart"} Visualization
                                </p>
                              </div>
                              <div className="mt-2">
                                <p className="text-sm font-medium">Data:</p>
                                <pre className="text-xs mt-1 overflow-auto">
                                  {JSON.stringify(plot.data, null, 2)}
                                </pre>
                              </div>
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  </CardContent>
                </Card>
              )}
              
              {hypothesis.verdict && (
                <Card className={
                  hypothesis.verdict === "supported" ? "border-green-500" : 
                  hypothesis.verdict === "refuted" ? "border-red-500" : ""
                }>
                  <CardHeader>
                    <CardTitle className={
                      hypothesis.verdict === "supported" ? "text-green-600" : 
                      hypothesis.verdict === "refuted" ? "text-red-600" : ""
                    }>
                      Verdict: {hypothesis.verdict.charAt(0).toUpperCase() + hypothesis.verdict.slice(1)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>
                      {hypothesis.verdict === "supported" 
                        ? "The experiment results support the original hypothesis with statistical significance."
                        : "The experiment results do not support the original hypothesis."}
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}