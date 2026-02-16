"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/campaigns", label: "Campaigns" },
  { href: "/assets", label: "Assets" },
  { href: "/ai-studio", label: "AI Studio" },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <nav className="rounded-2xl border border-brand-100 bg-white/70 p-3 backdrop-blur">
      <ul className="flex gap-2">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className={`rounded-lg px-4 py-2 text-sm transition ${
                pathname.startsWith(link.href)
                  ? "bg-brand-500 text-white"
                  : "text-brand-700 hover:bg-brand-50"
              }`}
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

