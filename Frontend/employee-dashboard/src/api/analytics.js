import axios from "axios";

const API = "http://localhost:8000";

export const fetchSummary = async () => {
  const res = await axios.get(`${API}/analytics/summary`);
  return res.data;
};

export const fetchStatusBreakdown = async () => {
  const res = await axios.get(`${API}/analytics/status`);
  return res.data.by_status;
};

export const fetchPriorityBreakdown = async () => {
  const res = await axios.get(`${API}/analytics/priority`);
  return res.data.by_priority;
};

export const fetchTrends = async () => {
  const res = await axios.get(`${API}/analytics/trends`);
  return res.data;
};
