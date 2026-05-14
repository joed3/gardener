import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gardener",
  description: "Identify plants and log your finds",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#16a34a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="bg-garden-700 text-white shadow-md">
          <nav className="max-w-2xl mx-auto flex items-center justify-between px-4 py-3">
            <Link href="/" className="text-xl font-bold tracking-tight">
              🌿 Gardener
            </Link>
            <div className="flex gap-4 text-sm font-medium">
              <Link href="/" className="hover:underline">
                Identify
              </Link>
              <Link href="/garden" className="hover:underline">
                My Garden
              </Link>
            </div>
          </nav>
        </header>
        <main className="max-w-2xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
