import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  LineChart,
  Line,
} from "recharts";

const COLORS = ["#2563eb", "#16a34a", "#dc2626", "#ca8a04"];

export function StatusChart({ data }) {
  const chartData = Object.entries(data).map(([k, v]) => ({
    name: k,
    value: v,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie data={chartData} dataKey="value" nameKey="name" label>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function PriorityChart({ data }) {
  const chartData = Object.entries(data).map(([k, v]) => ({
    name: k,
    value: v,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={chartData}>
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="value" fill="#2563eb" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TrendChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="count" stroke="#16a34a" />
      </LineChart>
    </ResponsiveContainer>
  );
}
