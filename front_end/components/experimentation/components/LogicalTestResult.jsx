import React from "react";

const LogicalTestResult = ({ result }) => {
  const { truth_table } = result;

  return (
    <div className="bg-gray-100 p-4 rounded">
      <h3 className="font-semibold text-lg mb-2">Logical Test Result</h3>
      
      <table className="table-auto border mt-2">
        <thead>
          <tr>
            {Object.keys(truth_table[0]).map((col, i) => (
              <th key={i} className="border px-2">{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {truth_table.map((row, i) => (
            <tr key={i}>
              {Object.values(row).map((val, j) => (
                <td key={j} className="border px-2">{val.toString()}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LogicalTestResult;
