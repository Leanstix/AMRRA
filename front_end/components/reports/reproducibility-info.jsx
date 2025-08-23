import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Badge } from "../ui/badge";

export function ReproducibilityInfo({ hypothesis }) {
  const { reproducibilityInfo } = hypothesis;
  
  if (!reproducibilityInfo) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Reproducibility Information</CardTitle>
        </CardHeader>
        <CardContent>
          <p>No reproducibility information available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Reproducibility Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Random Seed</h3>
              <Badge variant="outline" className="text-lg font-mono">
                {reproducibilityInfo.randomSeed}
              </Badge>
            </div>
            <div>
              <h3 className="text-sm font-medium mb-2">Dataset Hash</h3>
              <Badge variant="outline" className="text-lg font-mono">
                {reproducibilityInfo.datasetHash}
              </Badge>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Environment Information</h3>
            <div className="bg-muted p-4 rounded-md">
              <div className="mb-2">
                <span className="font-medium">Python Version:</span> {reproducibilityInfo.environment.pythonVersion}
              </div>
              
              <h4 className="text-sm font-medium mb-2">Packages</h4>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Package</TableHead>
                    <TableHead>Version</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reproducibilityInfo.environment.packages.map((pkg, index) => (
                    <TableRow key={index}>
                      <TableCell>{pkg.name}</TableCell>
                      <TableCell>{pkg.version}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}