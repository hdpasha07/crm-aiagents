import axios from "axios";

const API = "http://localhost:8000";

export const fetchComplaints = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const res = await axios.get(`${API}/complaints?${params}`);
  return res.data;
};

export const fetchComplaintById = async (id) => {
  const res = await axios.get(`${API}/complaints/${id}`);
  return res.data;
};

export const updateComplaint = async (id, data) => {
  return axios.patch(`${API}/complaints/${id}`, data);
};

export const resolveComplaint = async (id) => {
  return axios.patch(`${API}/complaints/${id}`, {
    status: "resolved",
  });
};

export const deleteComplaint = async (id) => {
  return axios.delete(`${API}/complaints/${id}`);
};

export const fetchComplaintsByEmail = async (email) => {
  const res = await axios.get(`${API}/complaints/by-email/${email}`);
  return res.data;
};
