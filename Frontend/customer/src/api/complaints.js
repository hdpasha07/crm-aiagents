import axios from "axios";

const API = "http://localhost:8000";

export const submitComplaint = async (payload) => {
  try {
    const res = await axios.post(`${API}/api/complaints`, payload);
    return res.data;
  } catch (err) {
    if (err.response?.status === 404) {
      const res = await axios.post(`${API}/complaints`, payload);
      return res.data;
    }
    throw err;
  }
};
