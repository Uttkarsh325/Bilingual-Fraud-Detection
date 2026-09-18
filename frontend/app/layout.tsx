import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import Navbar from "@/components/layout/Navbar";

export const metadata: Metadata = {
  title: "FraudGuard AI — Multilingual Fraud Advisory",
  description:
    "Identify and understand financial scams and fraudulent messages through text and voice in Hindi, English, and regional Indian languages.",
  keywords: ["fraud detection", "UPI scam", "phishing", "RBI advisory", "multilingual AI"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-900 text-slate-100">
        <Navbar />
        <main className="flex flex-col min-h-[calc(100vh-4rem)]">{children}</main>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#1e293b",
              color: "#f1f5f9",
              border: "1px solid #334155",
            },
          }}
        />
      </body>
    </html>
  );
}
