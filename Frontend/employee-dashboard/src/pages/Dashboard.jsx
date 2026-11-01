import React from "react";

import { useEffect, useState } from "react";
import {
  fetchComplaints,
  resolveComplaint,
  deleteComplaint,
} from "../api/complaints";
import ComplaintCard from "../components/ComplaintCard";
import Filters from "../components/Filters";

export default function Dashboard() {
  const [complaints, setComplaints] = useState([]);
  const [filters, setFilters] = useState({ status: "", priority: "" });

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchComplaints(filters);
        const list = Array.isArray(data) ? data : data?.complaints || [];
        setComplaints(list);
      } catch (err) {
        console.error("Failed loading complaints:", err);
        setComplaints([]);
      }
    };

    loadData();
  }, [filters]);

  const handleResolve = async (id) => {
    try {
      await resolveComplaint(id);
      const data = await fetchComplaints(filters);
      setComplaints(Array.isArray(data) ? data : data?.complaints || []);
    } catch (err) {
      console.error("Failed to resolve complaint:", err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteComplaint(id);
      const data = await fetchComplaints(filters);
      setComplaints(Array.isArray(data) ? data : data?.complaints || []);
    } catch (err) {
      console.error("Failed to delete complaint:", err);
    }
  };

  return (
    <div className="p-6">
      <Filters filters={filters} setFilters={setFilters} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {complaints.map((c) => (
          <ComplaintCard
            key={c.id}
            complaint={c}
            onResolve={handleResolve}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
