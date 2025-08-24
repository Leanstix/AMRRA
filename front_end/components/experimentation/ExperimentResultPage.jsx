import React from "react";
import TTestResult from "./tests/TTestResult";
import ChiSquareResult from "./tests/ChiSquareResult";
import AnovaResult from "./tests/AnovaResult";
import LinearRegressionResult from "./tests/LinearRegressionResult";
import LogisticRegressionResult from "./tests/LogisticRegressionResult";
import LogicalTestResult from "./tests/LogicalTestResult";

const ExperimentResultPage = ({ data }) => {
  if (!data) return <p>No data available</p>;

  const renderResult = () => {
    switch (data.test) {
      case "ttest":
        return <TTestResult result={data} />;
      case "chi2":
        return <ChiSquareResult result={data} />;
      case "anova":
        return <AnovaResult result={data} />;
      case "linear_regression":
        return <LinearRegressionResult result={data} />;
      case "logistic_regression":
        return <LogisticRegressionResult result={data} />;
      case "logical":
        return <LogicalTestResult result={data} />;
      default:
        return <p>Unsupported test type</p>;
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Experiment Result</h2>
      {renderResult()}
    </div>
  );
};

export default ExperimentResultPage;
