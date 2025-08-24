import React from "react";

const LogisticRegressionResult = ({ result }) => {
  const { coefficients, intercept, accuracy } = result;

  return (
    <div className="bg-gray-100 p-4 rounded">
      <h3 className="font-semibold text-lg mb-2">Logistic Regression Result</h3>
      <p><strong>Intercept:</strong> {intercept}</p>
      <p><strong>Accuracy:</strong> {accuracy}</p>
      
      <h4 className="mt-4 font-semibold">Coefficients</h4>
      <ul>
        {coefficients.map((coef, i) => (
          <li key={i}>X{i+1}: {coef}</li>
        ))}
      </ul>
    </div>
  );
};

export default LogisticRegressionResult;
