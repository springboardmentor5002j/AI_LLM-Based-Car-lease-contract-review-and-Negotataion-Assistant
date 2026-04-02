import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip
} from "chart.js";

import { Line } from "react-chartjs-2";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Legend,
  Tooltip
);

function LoanChart({ apr, term }) {

  const labels = [];
  const costData = [];

  const monthlyRate = apr / 100 / 12;

  for (let i = 1; i <= term; i++) {
    labels.push(i);
    costData.push((monthlyRate * i * 1000).toFixed(2));
  }

  const data = {
    labels: labels,
    datasets: [
      {
        label: "Estimated Interest Growth",
        data: costData,
        borderColor: "blue",
        backgroundColor: "lightblue"
      }
    ]
  };

  return (
    <div style={{ width: "600px", margin: "auto" }}>
      <Line data={data} />
    </div>
  );
}

export default LoanChart;