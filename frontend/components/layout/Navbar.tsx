"use client";
import { NAV_ITEMS } from "@/lib/constants";
import type { NavPage } from "@/types";

interface NavbarProps {
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
}

export default function Navbar({ activePage, onNavigate }: NavbarProps) {
  return (
    <nav className="navbar">
      <span className="navbar-brand">UniCompare</span>
      <div className="navbar-pills">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-pill${activePage === item.id ? " active" : ""}`}
            onClick={() => onNavigate(item.id as NavPage)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
