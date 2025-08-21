import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Download, FileDown, FileText, Package } from "lucide-react";

export function ArtifactsDownload({ hypothesis }) {
  const { artifacts } = hypothesis;
  
  if (!artifacts) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Artifacts & Downloads</CardTitle>
        </CardHeader>
        <CardContent>
          <p>No artifacts available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Artifacts & Downloads</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-muted/50">
              <CardContent className="pt-6">
                <div className="flex flex-col items-center text-center space-y-3">
                  <FileText className="h-8 w-8" />
                  <div>
                    <h3 className="font-medium">Report Document</h3>
                    <p className="text-sm text-muted-foreground">
                      Complete report with all findings and visualizations
                    </p>
                  </div>
                  <Button disabled={!artifacts.report} className="w-full">
                    <Download className="mr-2 h-4 w-4" />
                    Download Report
                  </Button>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-muted/50">
              <CardContent className="pt-6">
                <div className="flex flex-col items-center text-center space-y-3">
                  <Package className="h-8 w-8" />
                  <div>
                    <h3 className="font-medium">Full Artifacts Bundle</h3>
                    <p className="text-sm text-muted-foreground">
                      Code, data, metrics, and configuration files
                    </p>
                  </div>
                  <Button disabled={!artifacts.bundle} className="w-full">
                    <Download className="mr-2 h-4 w-4" />
                    Download Bundle
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
          
          {artifacts.versions && artifacts.versions.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-2">Version History</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Version</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {artifacts.versions.map((version) => (
                    <TableRow key={version.id}>
                      <TableCell>{version.id}</TableCell>
                      <TableCell>{version.date}</TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button variant="outline" size="sm">
                            <FileDown className="mr-1 h-3 w-3" />
                            Report
                          </Button>
                          <Button variant="outline" size="sm">
                            <FileDown className="mr-1 h-3 w-3" />
                            Bundle
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          
          <div className="text-sm text-muted-foreground">
            <p>Artifacts include:</p>
            <ul className="list-disc pl-5 mt-1 space-y-1">
              <li>plan.json - Preregistered experiment plan</li>
              <li>run.py - Experiment code</li>
              <li>metrics.json - Raw metrics and results</li>
              <li>plots/ - Generated visualizations</li>
              <li>environment.yml - Environment configuration</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}