import { useState } from "react";
import { submitComplaint } from "../api/complaints";
import { AlertCircle, CheckCircle2, Send } from "lucide-react";

export default function ComplaintForm({ orderId, email }) {
  const [text, setText] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!text.trim()) {
      return;
    }

    setLoading(true);
    try {
      const data = await submitComplaint({
        email,
        order_id: orderId,
        complaint_text: text,
      });
      setStatus(data?.message ?? "Complaint submitted successfully.");
      setText("");
    } catch (err) {
      console.error(err);
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  if (status && status !== "error") {
    return (
      <div className="flex items-start gap-3 p-4 bg-green-50 text-green-700 rounded-xl border border-green-100 animate-in fade-in duration-300">
        <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
        <p className="font-medium text-sm whitespace-pre-line">{status}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <textarea
        placeholder="Describe your issue with this order..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="w-full p-4 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400 transition-all resize-none h-24 text-sm"
      />

      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={loading || !text.trim()}
          className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        >
          {loading ? (
            <span>Submitting...</span>
          ) : (
            <>
              <Send size={16} />
              <span>Submit Complaint</span>
            </>
          )}
        </button>
      </div>

      {status === "error" && (
        <div className="flex items-center gap-2 text-red-600 text-sm mt-2">
          <AlertCircle size={16} />
          <p>Failed to submit complaint. Please try again.</p>
        </div>
      )}
    </div>
  );
}
