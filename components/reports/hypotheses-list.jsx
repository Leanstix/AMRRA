import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Badge } from "../ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Slider } from "../ui/slider";

export function HypothesesList({ hypotheses, onHypothesisSelect }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [effectSizeThreshold, setEffectSizeThreshold] = useState(0);

  const filteredHypotheses = hypotheses.filter((hypothesis) => {
    // Search filter
    const matchesSearch = 
      hypothesis.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hypothesis.paper.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hypothesis.claim.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Status filter
    const matchesStatus = 
      statusFilter === "all" || 
      hypothesis.status === statusFilter;
    
    // Effect size filter (only for completed hypotheses)
    const matchesEffectSize = 
      hypothesis.status !== "completed" || 
      !hypothesis.metrics?.effectSize ||
      hypothesis.metrics.effectSize >= effectSizeThreshold;
    
    return matchesSearch && matchesStatus && matchesEffectSize;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hypotheses List</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <Input
                placeholder="Search by ID, paper, or claim..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-sm font-medium">Min Effect Size: {effectSizeThreshold.toFixed(2)}</label>
              </div>
              <Slider
                value={[effectSizeThreshold]}
                min={0}
                max={1}
                step={0.05}
                onValueChange={(value) => setEffectSizeThreshold(value[0])}
              />
            </div>
          </div>
          
          {/* Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Paper</TableHead>
                <TableHead>Claim</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Verdict</TableHead>
                <TableHead>Effect Size</TableHead>
                <TableHead>p-value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredHypotheses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-4">
                    No hypotheses found matching your filters
                  </TableCell>
                </TableRow>
              ) : (
                filteredHypotheses.map((hypothesis) => (
                  <TableRow 
                    key={hypothesis.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => onHypothesisSelect(hypothesis)}
                  >
                    <TableCell className="font-medium">{hypothesis.id}</TableCell>
                    <TableCell>{hypothesis.paper}</TableCell>
                    <TableCell className="max-w-xs truncate">{hypothesis.claim}</TableCell>
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
                    <TableCell>
                      {hypothesis.metrics?.pValue ? 
                        hypothesis.metrics.pValue.toFixed(4) : "-"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          
          <div className="text-sm text-muted-foreground">
            Showing {filteredHypotheses.length} of {hypotheses.length} hypotheses
          </div>
        </div>
      </CardContent>
    </Card>
  );
}