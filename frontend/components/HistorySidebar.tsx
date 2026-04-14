"use client";
import Link from "next/link";
import { useMemo, useState } from "react";

export type HistoryItem = {
  id: string;
  question_preview: string;
  created_at: string;
};

export default function HistorySidebar({ items }: { items: HistoryItem[] }) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(
    () => items.filter((i) => i.question_preview.toLowerCase().includes(query.toLowerCase())),
    [items, query]
  );

  return (
    <aside className="w-full lg:w-80 border-r border-slate-200 bg-white h-full flex flex-col">
      <div className="p-4 border-b border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800">History</h2>
        <input
          type="text"
          placeholder="Search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="mt-2 w-full rounded border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="p-6 text-sm text-slate-500">
            <p className="font-semibold text-slate-700 mb-1">No history yet</p>
            <p className="mb-3">Your saved questions will appear here.</p>
            <Link href="/" className="text-indigo-600 font-semibold">Ask a question</Link>
          </div>
        ) : (
          <ul className="divide-y divide-slate-200">
            {filtered.map((item) => (
              <li key={item.id} className="p-4 hover:bg-slate-50">
                <Link href={`/history/${item.id}`} className="block">
                  <p className="text-sm font-semibold text-slate-800 line-clamp-2">{item.question_preview}</p>
                  <p className="text-xs text-slate-500 mt-1">{new Date(item.created_at).toLocaleString()}</p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
