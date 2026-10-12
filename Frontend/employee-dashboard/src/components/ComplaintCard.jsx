import React from "react";

export default function ComplaintCard({ complaint, onResolve, onDelete }) {
  return (
    <div className="bg-white p-4 rounded shadow">
      <div className="flex justify-between">
        <div>
          <p className="font-semibold">{complaint.email}</p>
          <p className="text-sm text-gray-500">Order: {complaint.order_id}</p>
        </div>
        <span className="text-sm px-2 py-1 rounded bg-gray-200">
          {complaint.status}
        </span>
      </div>

      <p className="mt-2">{complaint.complaint_text}</p>

      <div className="mt-2 flex gap-2 text-sm">
        <span>Priority: {complaint.priority || "N/A"}</span>
        <span>Escalated: {complaint.escalation_required ? "Yes" : "No"}</span>
        <span>Email Sent: {complaint.email_sent ? "Yes" : "No"}</span>
      </div>

      <div className="mt-4 flex gap-2">
        {complaint.status !== "resolved" && (
          <button
            onClick={() => onResolve(complaint.id)}
            className="bg-green-600 text-white px-3 py-1 rounded"
          >
            Mark Resolved
          </button>
        )}
        <button
          onClick={() => onDelete(complaint.id)}
          className="bg-red-600 text-white px-3 py-1 rounded"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
