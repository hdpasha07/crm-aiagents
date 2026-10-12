import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { ArrowRight, Lock } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    // Simulate delay for effect
    await new Promise(r => setTimeout(r, 600));
    window.history.replaceState(null, "", "/");
    login(email);
    setLoading(false);
  }

  return (
    <div className="flex justify-center items-center h-screen bg-gray-50/50">
      <div className="bg-white p-8 rounded-3xl shadow-xl shadow-blue-50 max-w-sm w-full border border-gray-100 animate-in fade-in zoom-in duration-500">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4 text-blue-600">
            <Lock size={32} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-gray-500 mt-2">Enter your email to continue</p>
        </div>

        <input
          placeholder="name@example.com"
          type="email"
          className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all font-medium text-gray-900 placeholder:text-gray-400"
          onChange={(e) => setEmail(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
        />

        <button
          onClick={handleLogin}
          disabled={loading || !email}
          className="w-full mt-6 py-4 bg-black text-white rounded-xl font-bold text-lg hover:bg-gray-800 transition-all flex items-center justify-center gap-2 shadow-lg shadow-gray-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Signing in..." : (
            <>
              <span>Sign In</span>
              <ArrowRight size={20} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
