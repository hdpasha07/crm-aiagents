import React from "react";

export default function Filters({ filters, setFilters }) {
  return (
    <div className="flex gap-4 mb-4">
      <select
        className="border p-2 rounded"
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
      >
        <option value="">All Status</option>
        <option value="new">New</option>
        <option value="escalated">Escalated</option>
        <option value="resolved">Resolved</option>
      </select>

      <select
        className="border p-2 rounded"
        value={filters.priority}
        onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
      >
        <option value="">All Priority</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>
    </div>
  );
}
