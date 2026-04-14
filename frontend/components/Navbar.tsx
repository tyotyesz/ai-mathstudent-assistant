"use client";
import Link from "next/link";
import { clearToken, getToken } from "../lib/auth";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(!!getToken());
  }, [pathname]);

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  return (
    <nav className="w-full bg-white shadow-sm border-b border-slate-200">
      <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm font-semibold text-slate-700">
          <Link href="/">Home</Link>
          {authed && <Link href="/profile">Profile</Link>}
          <span className="text-xs text-emerald-700 border border-emerald-300 px-2 py-1 rounded">Qwen math tutor</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {authed ? (
            <button onClick={handleLogout} className="text-rose-600 hover:text-rose-700 font-semibold">
              Logout
            </button>
          ) : (
            <div className="flex gap-3">
              <Link href="/login">Login</Link>
              <Link href="/register">Register</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
