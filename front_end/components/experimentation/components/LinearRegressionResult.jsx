import React from "react";

const LinearRegressionResult = ({ result }) => {
  const { coefficients, intercept, r_squared } = result;

  return (
    <div className="bg-gray-100 p-4 rounded">
      <h3 className="font-semibold text-lg mb-2">Linear Regression Result</h3>
      <p><strong>Intercept:</strong> {intercept}</p>
      <p><strong>R²:</strong> {r_squared}</p>
      
      <h4 className="mt-4 font-semibold">Coefficients</h4>
      <ul>
        {coefficients.map((coef, i) => (
          <li key={i}>X{i+1}: {coef}</li>
        ))}
      </ul>
    </div>
  );
};

export default LinearRegressionResult;
