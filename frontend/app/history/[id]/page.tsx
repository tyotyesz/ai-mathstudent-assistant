"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "../../../lib/api";
import { getToken } from "../../../lib/auth";
import MarkdownMath from "../../../components/MarkdownMath";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  category: string;
  problem_completed: boolean;
  created_at: string;
};

type ChatDetail = {
  id: string;
  title: string;
  is_completed: boolean;
  messages: ChatMessage[];
};

export default function HistoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<ChatDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    const load = async () => {
      try {
        const res = await api.get(`/api/qa/chats/${params.id}`);
        setData(res.data);
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [params.id, router]);

  if (loading) return <p>Loading...</p>;
  if (!data) return <p className="text-rose-600">Not found</p>;

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded shadow-sm p-4">
        <h1 className="text-xl font-semibold text-slate-800">{data.title}</h1>
        <p className="text-sm text-slate-600 mt-1">Conversation transcript</p>
      </div>
      <div className="bg-white border border-slate-200 rounded shadow-sm p-4 space-y-3">
        {data.messages.map((msg) => (
          <div key={msg.id} className={`p-3 rounded ${msg.role === "user" ? "bg-indigo-100" : "bg-slate-50 border border-slate-200"}`}>
            <p className="text-xs font-semibold uppercase text-slate-500">{msg.role}</p>
            <div className="mt-1">
              <MarkdownMath content={msg.content} className="text-sm text-slate-700 whitespace-pre-wrap" />
            </div>
          </div>
        ))}
      </div>
      <Link href="/" className="inline-flex items-center px-4 py-2 rounded bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700">
        Start new chat
      </Link>
    </div>
  );
}
