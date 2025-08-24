import React from "react";

const AnovaResult = ({ result }) => {
  const { f_statistic, p_value, groups } = result;

  return (
    <div className="bg-gray-100 p-4 rounded">
      <h3 className="font-semibold text-lg mb-2">ANOVA Result</h3>
      <p><strong>F-Statistic:</strong> {f_statistic}</p>
      <p><strong>P-Value:</strong> {p_value}</p>

      <h4 className="mt-4 font-semibold">Groups</h4>
      <table className="table-auto border mt-2">
        <thead>
          <tr>
            <th className="border px-2">Group</th>
            <th className="border px-2">Values</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((g, i) => (
            <tr key={i}>
              <td className="border px-2">{g.name}</td>
              <td className="border px-2">{g.values.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AnovaResult;
