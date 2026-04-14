import "../styles/globals.css";
import { ReactNode } from "react";
import Navbar from "../components/Navbar";
import { Toaster } from "react-hot-toast";

export const metadata = {
  title: "AI Math Tutor",
  description: "Qwen-powered mathematics tutoring assistant",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="app-container">
        <Navbar />
        <div className="mx-auto max-w-5xl px-4 py-6">{children}</div>
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
