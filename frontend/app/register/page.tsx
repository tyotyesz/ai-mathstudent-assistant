"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    if (password.length > 72) {
      setError("Password must be 72 characters or less.");
      setLoading(false);
      return;
    }
    try {
      await api.post("/api/auth/register", { email, password });
      router.push("/login");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (detail === "Email already registered") {
        setError("This email address is already in use.");
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white border border-slate-200 p-6 rounded shadow-sm">
      <h1 className="text-xl font-semibold text-slate-800">Register</h1>
      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <div>
          <label className="text-sm font-semibold text-slate-700" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-sm font-semibold text-slate-700" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-2 rounded bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Register"}
        </button>
      </form>
    </div>
  );
}
