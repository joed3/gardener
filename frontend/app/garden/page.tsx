"use client";

import { useEffect, useState } from "react";
import GardenGrid from "@/components/GardenGrid";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export type GardenEntry = {
  id: number;
  species: string;
  common_name: string;
  confidence: number;
  image_url: string;
  notes: string;
  captured_at: string;
  latitude: number | null;
  longitude: number | null;
};

export default function GardenPage() {
  const [entries, setEntries] = useState<GardenEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/garden`)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load garden: ${r.status}`);
        return r.json();
      })
      .then(setEntries)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Unknown error"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-400">
        Loading your garden…
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-garden-700">My Garden</h1>
        <p className="text-sm text-gray-500">{entries.length} plant{entries.length !== 1 ? "s" : ""} logged</p>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🌱</p>
          <p>Your garden is empty. Start by identifying a plant!</p>
        </div>
      ) : (
        <GardenGrid entries={entries} apiUrl={API} />
      )}
    </div>
  );
}
