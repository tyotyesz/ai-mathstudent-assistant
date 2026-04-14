"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { api } from "../../lib/api";
import { clearToken, getToken } from "../../lib/auth";

type ChatItem = {
  id: string;
  title: string;
  latest_preview: string;
  updated_at: string;
};

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [email, setEmail] = useState("");
  const [items, setItems] = useState<ChatItem[]>([]);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    const load = async () => {
      try {
        const [meRes, chatRes] = await Promise.all([
          api.get("/api/auth/me"),
          api.get("/api/qa/chats"),
        ]);
        setEmail(meRes.data.email);
        setItems(chatRes.data.items);
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [router]);

  const handleChangePassword = async () => {
    if (!oldPassword.trim() || !newPassword.trim()) {
      toast.error("Please fill in both password fields");
      return;
    }
    if (oldPassword === newPassword) {
      toast.error("Old password and new password must be different");
      return;
    }
    setPasswordSaving(true);
    try {
      await api.put("/api/auth/me/password", {
        old_password: oldPassword,
        new_password: newPassword,
      });
      toast.success("Password changed successfully");
      setOldPassword("");
      setNewPassword("");
      setShowPasswordModal(false);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(detail || "Failed to change password");
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmed = window.confirm("Are you sure you want to delete your account? This action cannot be undone.");
    if (!confirmed) return;
    setDeleting(true);
    try {
      await api.delete("/api/auth/me");
      clearToken();
      toast.success("Account deleted");
      router.replace("/register");
    } catch {
      toast.error("Failed to delete account");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div className="space-y-5">
      <div className="bg-white border border-slate-200 rounded shadow-sm p-4">
        <h1 className="text-xl font-semibold text-slate-800">Profile</h1>
        <p className="text-sm text-slate-600 mt-1">Email: {email}</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={() => setShowPasswordModal(true)}
            className="px-3 py-2 rounded border border-indigo-500 text-indigo-600 text-sm font-semibold hover:bg-indigo-50"
          >
            Change password
          </button>
          <button
            onClick={handleDeleteAccount}
            disabled={deleting}
            className="px-3 py-2 rounded border border-rose-500 text-rose-600 text-sm font-semibold hover:bg-rose-50 disabled:opacity-60"
          >
            {deleting ? "Deleting..." : "Delete account"}
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded shadow-sm p-4">
        <h2 className="text-lg font-semibold text-slate-800">Saved chats</h2>
        {items.length === 0 ? (
          <p className="text-sm text-slate-600 mt-2">No chats saved yet.</p>
        ) : (
          <ul className="mt-3 divide-y divide-slate-200">
            {items.map((item) => (
              <li key={item.id} className="py-3">
                <Link href={`/history/${item.id}`} className="text-indigo-700 font-semibold">
                  {item.title}
                </Link>
                <p className="text-sm text-slate-600 mt-1">{item.latest_preview}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {showPasswordModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center px-4 z-40">
          <div className="w-full max-w-md bg-white rounded border border-slate-200 shadow p-4">
            <h3 className="text-lg font-semibold text-slate-800">Change password</h3>
            <div className="mt-3 space-y-3">
              <div>
                <label htmlFor="oldPassword" className="text-sm font-semibold text-slate-700">Old password</label>
                <input
                  id="oldPassword"
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label htmlFor="newPassword" className="text-sm font-semibold text-slate-700">New password</label>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowPasswordModal(false)}
                className="px-3 py-2 rounded border border-slate-300 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleChangePassword}
                disabled={passwordSaving}
                className="px-3 py-2 rounded bg-indigo-600 text-white text-sm font-semibold disabled:opacity-50"
              >
                {passwordSaving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
