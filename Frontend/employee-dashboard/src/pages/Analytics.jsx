
import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import {
  TrendingUp, AlertCircle, CheckCircle, Clock,
  Activity, BarChart2, PieChart as PieChartIcon, Calendar
} from 'lucide-react';
import {
  fetchSummary,
  fetchStatusBreakdown,
  fetchPriorityBreakdown,
  fetchTrends
} from '../api/analytics';

const Analytics = () => {
  const [summary, setSummary] = useState(null);
  const [statusData, setStatusData] = useState([]);
  const [priorityData, setPriorityData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [summaryRes, statusRes, priorityRes, trendsRes] = await Promise.all([
          fetchSummary(),
          fetchStatusBreakdown(),
          fetchPriorityBreakdown(),
          fetchTrends()
        ]);

        setSummary(summaryRes);

        // Transform Object data to Array for Recharts
        const formattedStatus = Object.entries(statusRes || {}).map(([key, value]) => ({
          name: key.charAt(0).toUpperCase() + key.slice(1),
          value: value,
          color: getStatusColor(key)
        }));
        setStatusData(formattedStatus);

        const formattedPriority = Object.entries(priorityRes || {}).map(([key, value]) => ({
          name: key.charAt(0).toUpperCase() + key.slice(1),
          value: value,
          color: getPriorityColor(key)
        }));
        setPriorityData(formattedPriority);

        setTrendData(trendsRes || []);

      } catch (err) {
        console.error("Failed to load analytics data", err);
        setError("Failed to load analytics data. Please make sure the server is running.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f59e0b',
      resolved: '#22c55e',
      escalated: '#a855f7',
      inprogress: '#3b82f6'
    };
    return colors[status?.toLowerCase()] || '#94a3b8';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: '#ef4444',
      medium: '#f59e0b',
      low: '#3b82f6'
    };
    return colors[priority?.toLowerCase()] || '#94a3b8';
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[600px]">
      <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent"></div>
    </div>
  );

  if (error) return (
    <div className="p-8 text-center text-red-500 bg-red-50 rounded-2xl border border-red-100 m-6">
      <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
      {error}
    </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-10">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Analytics Dashboard</h1>
          <p className="text-gray-500 mt-2 text-lg">Real-time insights and performance metrics.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500 bg-white px-4 py-2 rounded-xl border border-gray-100 shadow-sm">
          <Calendar className="w-4 h-4" />
          <span>Real-time Data</span>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Complaints"
          value={summary?.total_complaints || 0}
          icon={Activity}
          color="blue"
          subtext="Total processed tickets"
        />
        <KPICard
          title="Resolved"
          value={summary?.resolved || 0}
          icon={CheckCircle}
          color="green"
          subtext={`${summary?.resolution_rate || 0}% Resolution Rate`}
        />
        <KPICard
          title="Escalated"
          value={summary?.escalated || 0}
          icon={TrendingUp}
          color="purple"
          subtext={`${summary?.escalation_rate || 0}% Escalation Rate`}
        />
        <KPICard
          title="Pending Action"
          value={(summary?.total_complaints || 0) - (summary?.resolved || 0)}
          icon={Clock}
          color="amber"
          subtext="Requires attention"
        />
      </div>

      {/* Charts Section 1: Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Distribution */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-gray-400" />
              By Priority
            </h2>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityData} layout="vertical" margin={{ left: 0, right: 30 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" hide />
                <YAxis
                  dataKey="name"
                  type="category"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  width={60}
                />
                <Tooltip
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={32}>
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Distribution */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <PieChartIcon className="w-5 h-5 text-gray-400" />
              Status Breakdown
            </h2>
          </div>
          <div className="h-[300px] w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Section 2: Trends */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-gray-400" />
            Complaint Activity Trend
          </h2>
        </div>
        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: 12 }}
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#2563eb"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorCount)"
                name="Complaints"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

const KPICard = ({ title, value, icon: Icon, color, subtext }) => {
  const colorStyles = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl ${colorStyles[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-1 font-medium">{title}</div>
      {subtext && (
        <div className="text-xs text-gray-400 mt-3 pt-3 border-t border-gray-50 flex items-center gap-1">
          {subtext}
        </div>
      )}
    </div>
  );
};

export default Analytics;
