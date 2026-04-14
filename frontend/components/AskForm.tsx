"use client";
import { FormEvent, useState } from "react";
import { api } from "../lib/api";
import AnswerPanel from "./AnswerPanel";
import ErrorPanel from "./ErrorPanel";
import toast from "react-hot-toast";

export type QAItem = {
  id: string;
  question: string;
  answer: string;
  steps: string[];
  created_at: string;
};

type Props = {
  onSaved: (item: QAItem) => void;
};

export default function AskForm({ onSaved }: Props) {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<QAItem | null>(null);
  const [lastPayload, setLastPayload] = useState<string>("");

  const validate = (text: string) => {
    if (!text || text.trim().length === 0) return "Question cannot be empty";
    if (text.trim().length > 300) return "Question must be 300 characters or less";
    return null;
  };

  const submit = async (payload: string) => {
    setError(null);
    setServerError(null);
    setLoading(true);
    try {
      const res = await api.post("/api/qa/ask", { question: payload.trim() });
      setAnswer(res.data);
      onSaved(res.data);
      toast.success("Saved to history");
    } catch (err) {
      setServerError("The service is unavailable or timed out. Please retry.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationError = validate(question);
    if (validationError) {
      setError(validationError);
      return;
    }
    setLastPayload(question);
    await submit(question);
  };

  const handleRetry = async () => {
    if (!lastPayload) return;
    await submit(lastPayload);
  };

  return (
    <div className="flex flex-col">
      <form onSubmit={handleSubmit} className="rounded border border-slate-200 bg-white p-4 shadow-sm">
        <label className="text-sm font-semibold text-slate-700" htmlFor="question">
          Ask a math question
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm h-28"
          placeholder="Example: x^2 - 5x + 6 = 0"
        />
        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-slate-500">Demo mode (no real AI). Math-only.</span>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center px-4 py-2 rounded bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>
      </form>
      {serverError && <ErrorPanel message={serverError} onRetry={handleRetry} />}
      {answer && !serverError && <AnswerPanel answer={answer.answer} steps={answer.steps} />}
    </div>
  );
}
