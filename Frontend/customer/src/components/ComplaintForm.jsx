import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { submitComplaint } from "../api/complaints";
import { AlertCircle, CheckCircle2, Clock, Send, RotateCcw, RefreshCw, ShieldAlert } from "lucide-react";

export default function ComplaintForm({ orderId, email }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [isEscalated, setIsEscalated] = useState(false);
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!text.trim() || loading) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await submitComplaint({
        email,
        order_id: orderId,
        complaint_text: text,
      });

      const blockedOrInvalid =
        res?.is_valid === false ||
        res?.guardrail_triggered === true ||
        res?.status === "invalid" ||
        res?.status === "spam" ||
        res?.success === false;

      const escalated = !blockedOrInvalid && Boolean(res?.escalation_required);

      if (blockedOrInvalid) {
        setIsInvalid(true);
        setIsEscalated(false);
        setResponse(
          res?.message ||
          res?.response ||
          "For your security, please do not share financial information here. How can I assist you with your order?"
        );
      } else if (escalated) {
        setIsInvalid(false);
        setIsEscalated(true);
        setResponse("Your issue has been escalated to our support team. We will get back with you shortly.");
      } else {
        setIsInvalid(false);
        setIsEscalated(false);
        setResponse(res?.ai_response || res?.response || res?.resolution || res?.message || "");
      }
    } catch (err) {
      console.error("Failed to submit complaint:", err);
      setError("Failed to submit complaint. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setText("");
    setResponse(null);
    setIsEscalated(false);
    setIsInvalid(false);
    setError(null);
  };

  return (
    <div className="space-y-3">
      <textarea
        placeholder="Describe your issue with this order..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading || !!response}
        className="w-full p-4 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-red-400 transition-all resize-none h-24 text-sm disabled:bg-gray-50 disabled:text-gray-600"
      />

      {!response && (
        <div className="flex justify-end">
          <button
            onClick={handleSubmit}
            disabled={loading || !text.trim()}
            className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <Send size={16} />
                <span>Submit Complaint</span>
              </>
            )}
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm mt-2">
          <AlertCircle size={16} />
          <p>{error}</p>
        </div>
      )}

      {response && (
        <div
          className={`p-4 rounded-xl border transition-all animate-in fade-in slide-in-from-top-2 duration-300 ${
            isInvalid
              ? "bg-rose-50/70 border-rose-200 text-rose-950"
              : isEscalated
              ? "bg-amber-50/70 border-amber-200 text-amber-950"
              : "bg-emerald-50/70 border-emerald-200 text-emerald-950"
          }`}
        >
          <div className="flex items-start gap-3">
            {isInvalid ? (
              <ShieldAlert className="w-5 h-5 text-rose-600 mt-0.5 shrink-0" />
            ) : isEscalated ? (
              <Clock className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
            )}
            <div className="flex-1 space-y-2 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                  {isInvalid ? "Notice" : isEscalated ? "Escalation Notice" : "AGENT RESOLUTION"}
                </p>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    isInvalid
                      ? "bg-rose-100 text-rose-800 border border-rose-200"
                      : isEscalated
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800"
                  }`}
                >
                  {isInvalid ? "Invalid Input" : isEscalated ? "Escalated" : "Resolved"}
                </span>
              </div>
              <div className="text-sm text-gray-800 leading-relaxed break-words">
                <ReactMarkdown
                  components={{
                    p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-2 space-y-1" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-2 space-y-1" {...props} />,
                    li: ({ node, ...props }) => <li className="pl-0.5" {...props} />,
                    strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
                    h1: ({ node, ...props }) => <h1 className="text-base font-bold mb-2 text-gray-900" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-sm font-bold mb-1.5 text-gray-900" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-sm font-semibold mb-1 text-gray-900" {...props} />,
                  }}
                >
                  {response}
                </ReactMarkdown>
              </div>
              {isInvalid && (
                <p className="text-xs text-rose-600 font-medium pt-1">
                  Please update your message and try again.
                </p>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-gray-200/60 flex justify-end">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 hover:text-gray-900 shadow-sm transition-all"
            >
              <RotateCcw size={14} />
              <span>{isInvalid ? "Try Again" : "Submit Another Ticket"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
