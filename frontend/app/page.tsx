"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { api } from "../lib/api";
import { getToken } from "../lib/auth";

type Folder = {
  id: string;
  name: string;
  chat_count: number;
  created_at: string;
};

type ChatListItem = {
  id: string;
  title: string;
  folder_id: string | null;
  is_completed: boolean;
  latest_preview: string;
  updated_at: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  category: "task_generation" | "problem_solving" | "follow_up" | "non_math";
  problem_completed: boolean;
  created_at: string;
};

type ChatDetail = {
  id: string;
  title: string;
  folder_id: string | null;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
};

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");
  const [folderName, setFolderName] = useState("");
  const [selectedFolderId, setSelectedFolderId] = useState<string>("all");
  const [folders, setFolders] = useState<Folder[]>([]);
  const [chats, setChats] = useState<ChatListItem[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [selectedChat, setSelectedChat] = useState<ChatDetail | null>(null);

  const loadSidebar = async () => {
    const [foldersRes, chatsRes] = await Promise.all([
      api.get("/api/qa/folders"),
      api.get("/api/qa/chats"),
    ]);
    setFolders(foldersRes.data.items);
    setChats(chatsRes.data.items);
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    const load = async () => {
      try {
        await loadSidebar();
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [router]);

  useEffect(() => {
    if (!selectedChatId) {
      setSelectedChat(null);
      return;
    }
    const loadChat = async () => {
      try {
        const res = await api.get(`/api/qa/chats/${selectedChatId}`);
        setSelectedChat(res.data);
      } catch {
        toast.error("Could not load chat");
      }
    };
    loadChat();
  }, [selectedChatId]);

  const filteredChats = useMemo(() => {
    if (selectedFolderId === "all") return chats;
    if (selectedFolderId === "none") return chats.filter((chat) => !chat.folder_id);
    return chats.filter((chat) => chat.folder_id === selectedFolderId);
  }, [chats, selectedFolderId]);

  const submitMessage = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    setSending(true);
    try {
      if (!selectedChatId) {
        const res = await api.post("/api/qa/chats/start", { message: trimmed });
        setSelectedChat(res.data);
        setSelectedChatId(res.data.id);
        toast.success("Chat saved");
      } else {
        const res = await api.post(`/api/qa/chats/${selectedChatId}/messages`, { message: trimmed });
        setSelectedChat(res.data);
      }
      setMessage("");
      await loadSidebar();
    } catch {
      toast.error("The tutor service is unavailable right now");
    } finally {
      setSending(false);
    }
  };

  const createFolder = async () => {
    const name = folderName.trim();
    if (!name) return;
    try {
      await api.post("/api/qa/folders", { name });
      setFolderName("");
      toast.success("Folder created");
      await loadSidebar();
    } catch {
      toast.error("Could not create folder");
    }
  };

  const deleteChat = async (chatId: string) => {
    const confirmed = window.confirm("Are you sure you want to delete this chat?");
    if (!confirmed) return;
    try {
      await api.delete(`/api/qa/chats/${chatId}`);
      toast.success("Chat deleted");
      if (selectedChatId === chatId) {
        setSelectedChatId(null);
        setSelectedChat(null);
      }
      await loadSidebar();
    } catch {
      toast.error("Could not delete chat");
    }
  };

  const deleteFolder = async (folder: Folder) => {
    const prompt =
      folder.chat_count > 0
        ? "Are you sure you want to delete this folder? The chats inside it will also be deleted."
        : "Are you sure you want to delete this folder?";
    const confirmed = window.confirm(prompt);
    if (!confirmed) return;
    try {
      await api.delete(`/api/qa/folders/${folder.id}`);
      toast.success("Folder deleted");
      if (selectedFolderId === folder.id) {
        setSelectedFolderId("all");
      }
      if (selectedChatId) {
        const stillExists = chats.some((chat) => chat.id === selectedChatId && chat.folder_id !== folder.id);
        if (!stillExists) {
          setSelectedChatId(null);
          setSelectedChat(null);
        }
      }
      await loadSidebar();
    } catch {
      toast.error("Could not delete folder");
    }
  };

  const moveChatToFolder = async (chatId: string, folderId: string) => {
    try {
      await api.patch(`/api/qa/chats/${chatId}/folder`, {
        folder_id: folderId === "none" ? null : folderId,
      });
      await loadSidebar();
      if (selectedChatId === chatId) {
        const updated = await api.get(`/api/qa/chats/${chatId}`);
        setSelectedChat(updated.data);
      }
    } catch {
      toast.error("Could not move chat");
    }
  };

  const categoryLabel = (category: ChatMessage["category"]) => {
    if (category === "task_generation") return "Task generation";
    if (category === "problem_solving") return "Problem solving";
    if (category === "follow_up") return "Follow-up";
    return "Non-math refusal";
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
      <aside className="bg-white border border-slate-200 rounded p-4 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Folders</h2>
          <div className="mt-2 flex gap-2">
            <input
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="New folder"
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            />
            <button onClick={createFolder} className="px-3 py-2 rounded bg-slate-800 text-white text-sm">
              Add
            </button>
          </div>
          <select
            className="mt-3 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={selectedFolderId}
            onChange={(e) => setSelectedFolderId(e.target.value)}
          >
            <option value="all">All chats</option>
            <option value="none">Without folder</option>
            {folders.map((folder) => (
              <option key={folder.id} value={folder.id}>
                {folder.name} ({folder.chat_count})
              </option>
            ))}
          </select>
          <ul className="mt-3 space-y-2">
            {folders.map((folder) => (
              <li key={folder.id} className="flex items-center justify-between text-sm border border-slate-200 rounded px-2 py-1">
                <button onClick={() => setSelectedFolderId(folder.id)} className="text-slate-700 hover:text-slate-900">
                  {folder.name}
                </button>
                <button onClick={() => deleteFolder(folder)} className="text-rose-600">Delete</button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-800">Chats</h3>
            <button
              className="text-sm text-indigo-600 font-semibold"
              onClick={() => {
                setSelectedChatId(null);
                setSelectedChat(null);
              }}
            >
              New chat
            </button>
          </div>
          <ul className="mt-3 space-y-2 max-h-[420px] overflow-auto">
            {filteredChats.map((chat) => (
              <li key={chat.id} className={`border rounded p-2 ${selectedChatId === chat.id ? "border-indigo-500" : "border-slate-200"}`}>
                <button className="text-left w-full" onClick={() => setSelectedChatId(chat.id)}>
                  <p className="text-sm font-semibold text-slate-800 truncate">{chat.title}</p>
                  <p className="text-xs text-slate-600 mt-1 line-clamp-2">{chat.latest_preview}</p>
                </button>
                <div className="mt-2 flex items-center gap-2">
                  <select
                    className="text-xs border border-slate-300 rounded px-2 py-1"
                    value={chat.folder_id || "none"}
                    onChange={(e) => moveChatToFolder(chat.id, e.target.value)}
                  >
                    <option value="none">No folder</option>
                    {folders.map((folder) => (
                      <option key={folder.id} value={folder.id}>{folder.name}</option>
                    ))}
                  </select>
                  <button onClick={() => deleteChat(chat.id)} className="text-xs text-rose-600">Delete</button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      <main className="bg-white border border-slate-200 rounded p-4">
        <h1 className="text-2xl font-semibold text-slate-900">Math Tutor Chat</h1>
        <p className="text-sm text-slate-600 mt-1">
          English-only, mathematics-only tutoring. Ask for a new task, help with solving, or follow-up hints.
        </p>

        <div className="mt-4 border border-slate-200 rounded p-3 h-[480px] overflow-auto space-y-3 bg-slate-50">
          {!selectedChat && (
            <p className="text-sm text-slate-600">
              Start a new math session by sending a message. The tutor will guide you one step at a time.
            </p>
          )}
          {selectedChat?.messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[90%] rounded p-3 ${msg.role === "user" ? "ml-auto bg-indigo-100" : "mr-auto bg-white border border-slate-200"}`}
            >
              <p className="text-sm text-slate-700 whitespace-pre-wrap">{msg.content}</p>
              {msg.role === "assistant" && (
                <div className="mt-2 flex items-center justify-between gap-2 text-xs text-slate-500">
                  <span>{categoryLabel(msg.category)}</span>
                  {msg.problem_completed && <span className="font-semibold text-emerald-700">Problem completed</span>}
                </div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={submitMessage} className="mt-4 space-y-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Example: Give me a quadratic equation problem"
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm h-28"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">
              The tutor gives only the next hint/step unless the problem is already completed.
            </span>
            <button
              type="submit"
              disabled={sending}
              className="inline-flex px-4 py-2 rounded bg-indigo-600 text-white text-sm font-semibold disabled:opacity-50"
            >
              {sending ? "Sending..." : selectedChatId ? "Send follow-up" : "Start chat"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
