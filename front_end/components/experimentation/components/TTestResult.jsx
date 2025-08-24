import React from "react";

const TTestResult = ({ result }) => {
  const { hypothesis, t_statistic, p_value, confidence_interval } = result;

  return (
    <div className="bg-gray-100 p-4 rounded">
      <h3 className="font-semibold text-lg mb-2">T-Test Result</h3>
      <p><strong>Hypothesis:</strong> {hypothesis}</p>
      <p><strong>T-Statistic:</strong> {t_statistic}</p>
      <p><strong>P-Value:</strong> {p_value}</p>
      {confidence_interval && (
        <p><strong>Confidence Interval:</strong> {confidence_interval.join(" - ")}</p>
      )}
    </div>
  );
};

export default TTestResult;
