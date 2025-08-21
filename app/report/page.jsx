"use client";

import React, { useState } from "react";
import { MainLayout } from "@/components/layout/main-layout";

// Mock data to prevent the undefined error
const mockHypotheses = [
  {
    id: "H1",
    paper: "Smith et al. (2023)",
    status: "Completed",
    metrics: { effectSize: 0.75, pValue: 0.02 },
    verdict: "Supported",
    plan: "Test plan for hypothesis 1",
    code: "import numpy as np\n\ndef run_experiment():\n    return True",
    seed: "12345",
    datasetHash: "abc123def456",
    environment: "Python 3.9",
    plots: []
  },
  {
    id: "H2",
    paper: "Johnson et al. (2022)",
    status: "Running",
    metrics: { effectSize: 0.45, pValue: 0.08 },
    verdict: "Pending",
    plan: "Test plan for hypothesis 2",
    code: "import pandas as pd\n\ndef analyze_data():\n    return True",
    seed: "67890",
    datasetHash: "xyz789abc012",
    environment: "Python 3.8",
    plots: []
  }
];

const ReportsTab = ({ hypotheses = mockHypotheses }) => {
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);
  const [filterStatus, setFilterStatus] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredHypotheses = hypotheses.filter((h) => {
    const statusMatch = filterStatus === "All" || h.status === filterStatus;
    const searchMatch =
      h.paper.toLowerCase().includes(searchQuery.toLowerCase()) ||
      h.id.toLowerCase().includes(searchQuery.toLowerCase());
    return statusMatch && searchMatch;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Overview / Dashboard */}
      <div className="bg-gray-100 p-4 rounded shadow">
        <h2 className="text-xl font-bold mb-2">Overview / Dashboard</h2>
        <p>Total Hypotheses: {hypotheses.length}</p>
        <p>Completed: {hypotheses.filter((h) => h.status === "Completed").length}</p>
        <p>Running: {hypotheses.filter((h) => h.status === "Running").length}</p>
        <p>Failed: {hypotheses.filter((h) => h.status === "Failed").length}</p>
        <p>
          Average Effect Size:{" "}
          {(
            hypotheses.reduce((acc, h) => acc + (h.metrics.effectSize || 0), 0) /
            (hypotheses.length || 1)
          ).toFixed(2)}
        </p>
      </div>

      {/* Hypotheses List */}
      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-xl font-bold mb-2">Hypotheses List</h2>
        <div className="flex space-x-4 mb-2">
          <select
            className="border p-1 rounded"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="All">All</option>
            <option value="Completed">Completed</option>
            <option value="Running">Running</option>
            <option value="Failed">Failed</option>
          </select>
          <input
            type="text"
            placeholder="Search by ID or Paper"
            className="border p-1 rounded flex-1"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <table className="w-full border-collapse border border-gray-300">
          <thead className="bg-gray-200">
            <tr>
              <th className="border p-2">ID</th>
              <th className="border p-2">Paper / Claim</th>
              <th className="border p-2">Status</th>
              <th className="border p-2">Effect Size</th>
            </tr>
          </thead>
          <tbody>
            {filteredHypotheses.map((h) => (
              <tr
                key={h.id}
                className="cursor-pointer hover:bg-gray-100"
                onClick={() => setSelectedHypothesis(h)}
              >
                <td className="border p-2">{h.id}</td>
                <td className="border p-2">{h.paper}</td>
                <td className="border p-2">{h.status}</td>
                <td className="border p-2">{h.metrics.effectSize?.toFixed(2) || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detailed Hypothesis View */}
      {selectedHypothesis && (
        <div className="bg-gray-50 p-4 rounded shadow space-y-3">
          <h2 className="text-xl font-bold">Hypothesis Details: {selectedHypothesis.id}</h2>
          <div>
            <h3 className="font-semibold">Experiment Plan:</h3>
            <pre className="bg-white p-2 rounded">{selectedHypothesis.plan || "N/A"}</pre>
          </div>
          <div>
            <h3 className="font-semibold">Code (run.py):</h3>
            <pre className="bg-white p-2 rounded overflow-x-auto">{selectedHypothesis.code || "N/A"}</pre>
          </div>
          <div>
            <h3 className="font-semibold">Metrics:</h3>
            <ul>
              {selectedHypothesis.metrics &&
                Object.entries(selectedHypothesis.metrics).map(([k, v]) => (
                  <li key={k}>
                    {k}: {v.toFixed(2)}
                  </li>
                ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold">Verdict:</h3>
            <p>{selectedHypothesis.verdict || "Pending"}</p>
          </div>
          <div>
            <h3 className="font-semibold">Plots:</h3>
            <div className="flex space-x-2 overflow-x-auto">
              {selectedHypothesis.plots?.map((src, idx) => (
                <img key={idx} src={src} alt={`plot-${idx}`} className="h-32 rounded shadow" />
              )) || <p>N/A</p>}
            </div>
          </div>
          <div>
            <h3 className="font-semibold">Reproducibility Info:</h3>
            <p>Seed: {selectedHypothesis.seed}</p>
            <p>Dataset Hash: {selectedHypothesis.datasetHash}</p>
            <p>Environment: {selectedHypothesis.environment}</p>
          </div>
          <div className="flex space-x-2 mt-2">
            <button className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
              Download HTML
            </button>
            <button className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600">
              Download PDF
            </button>
            <button className="bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600">
              Download Full Artifacts
            </button>
            <button
              className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
              onClick={() => setSelectedHypothesis(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const ReportPage = () => {
  return (
    <MainLayout>
      <ReportsTab hypotheses={mockHypotheses} />
    </MainLayout>
  );
};

export default ReportPage;