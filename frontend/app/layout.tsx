import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import CustomCursor from "@/components/layout/CustomCursor";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "UniCompare — University Comparison Bot",
  description: "Compare universities using real student experiences, Reddit reviews, and AI-powered insights.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-gray-100 text-gray-900 antialiased min-h-screen" style={{ fontFamily: "var(--font-inter), Inter, sans-serif" }}>
        <CustomCursor />
        {children}
      </body>
    </html>
  );
}
