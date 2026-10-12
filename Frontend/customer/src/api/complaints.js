import axios from "axios";

const API = "http://localhost:8000";

export const submitComplaint = async (payload) => {
  const res = await axios.post(`${API}/complaints`, payload);
  return res.data;
};
