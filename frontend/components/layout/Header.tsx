"use client";
import type { NavPage } from "@/types";

const NAV = [
  { id: "home" as NavPage,         label: "Home" },
  { id: "about" as NavPage,        label: "About Us" },
  { id: "faq" as NavPage,          label: "FAQ" },
  { id: "universities" as NavPage, label: "Famous Universities" },
];

interface HeaderProps {
  active: NavPage;
  onNav: (p: NavPage) => void;
}

export default function Header({ active, onNav }: HeaderProps) {
  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <button
          onClick={() => onNav("home")}
          className="flex items-center gap-2 shrink-0 focus:outline-none"
        >
            <span className="text-xl font-extrabold tracking-tight">
            <span className="text-gray-900">Uni</span>
            <span className="text-blue-600">Compare</span>
          </span>
        </button>

        {/* Nav pills */}
        <nav className="flex items-center gap-1 overflow-x-auto scrollbar-hide">
          {NAV.map((item) => {
            const isActive = active === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNav(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold whitespace-nowrap transition-colors
                  ${isActive
                    ? "bg-blue-50 text-blue-600 border border-blue-200"
                    : "text-gray-500 hover:text-gray-800 hover:bg-gray-100 border border-transparent"
                  }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
