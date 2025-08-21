import React, { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { ReportsDashboard } from "./reports-dashboard";
import { HypothesesList } from "./hypotheses-list";
import { HypothesisDetail } from "./hypothesis-detail";
import { ReproducibilityInfo } from "./reproducibility-info";
import { ArtifactsDownload } from "./artifacts-download";
import { AnalyticsComparison } from "./analytics-comparison";
import { mockData } from "./mock-data";

export function ReportsPage() {
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  const handleHypothesisSelect = (hypothesis) => {
    setSelectedHypothesis(hypothesis);
    setActiveTab("detail");
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">ML Reproducibility Reports</h1>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-6 mb-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="hypotheses">Hypotheses</TabsTrigger>
          <TabsTrigger value="detail" disabled={!selectedHypothesis}>
            Hypothesis Detail
          </TabsTrigger>
          <TabsTrigger value="reproducibility" disabled={!selectedHypothesis}>
            Reproducibility
          </TabsTrigger>
          <TabsTrigger value="artifacts" disabled={!selectedHypothesis}>
            Artifacts
          </TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <ReportsDashboard data={mockData} onHypothesisSelect={handleHypothesisSelect} />
        </TabsContent>

        <TabsContent value="hypotheses" className="space-y-6">
          <HypothesesList 
            hypotheses={mockData.hypotheses} 
            onHypothesisSelect={handleHypothesisSelect} 
          />
        </TabsContent>

        <TabsContent value="detail" className="space-y-6">
          {selectedHypothesis && <HypothesisDetail hypothesis={selectedHypothesis} />}
        </TabsContent>

        <TabsContent value="reproducibility" className="space-y-6">
          {selectedHypothesis && <ReproducibilityInfo hypothesis={selectedHypothesis} />}
        </TabsContent>

        <TabsContent value="artifacts" className="space-y-6">
          {selectedHypothesis && <ArtifactsDownload hypothesis={selectedHypothesis} />}
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <AnalyticsComparison hypotheses={mockData.hypotheses} />
        </TabsContent>
      </Tabs>
    </div>
  );
}