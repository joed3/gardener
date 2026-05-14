"use client";

import { useState } from "react";
import Image from "next/image";
import type { GardenEntry } from "@/app/garden/page";

interface Props {
  entries: GardenEntry[];
  apiUrl: string;
}

export default function GardenGrid({ entries, apiUrl }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {entries.map((entry) => (
        <div key={entry.id}>
          <button
            onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
            className="w-full text-left rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden hover:shadow-md transition"
          >
            <div className="relative w-full aspect-square bg-garden-100">
              {entry.image_url ? (
                <Image
                  src={`${apiUrl}${entry.image_url}`}
                  alt={entry.common_name}
                  fill
                  className="object-cover"
                  sizes="(max-width: 640px) 50vw, 33vw"
                />
              ) : (
                <div className="flex items-center justify-center h-full text-3xl text-garden-300">
                  🌿
                </div>
              )}
            </div>
            <div className="p-2">
              <p className="text-sm font-semibold text-gray-800 truncate">{entry.common_name}</p>
              <p className="text-xs text-gray-400">
                {new Intl.DateTimeFormat(undefined, {
                  dateStyle: "medium",
                }).format(new Date(entry.captured_at))}
              </p>
            </div>
          </button>

          {expanded === entry.id && (
            <EntryDetail entry={entry} apiUrl={apiUrl} onClose={() => setExpanded(null)} />
          )}
        </div>
      ))}
    </div>
  );
}

function EntryDetail({
  entry,
  apiUrl,
  onClose,
}: {
  entry: GardenEntry;
  apiUrl: string;
  onClose: () => void;
}) {
  const hasCoords = entry.latitude !== null && entry.longitude !== null;
  const mapUrl = hasCoords
    ? `https://staticmap.openstreetmap.de/staticmap.php?center=${entry.latitude},${entry.longitude}&zoom=15&size=400x200&markers=${entry.latitude},${entry.longitude}`
    : null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-end sm:items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {entry.image_url && (
          <div className="relative w-full aspect-video bg-garden-100">
            <Image
              src={`${apiUrl}${entry.image_url}`}
              alt={entry.common_name}
              fill
              className="object-cover rounded-t-2xl"
              sizes="448px"
            />
          </div>
        )}

        <div className="p-5 space-y-3">
          <div>
            <h2 className="text-xl font-bold text-garden-700">{entry.common_name}</h2>
            <p className="text-sm text-gray-500 italic">{entry.species}</p>
            <p className="text-sm text-gray-500">
              Confidence: {Math.round(entry.confidence * 100)}%
            </p>
          </div>

          <div className="text-sm text-gray-600 space-y-1">
            <p>
              📅{" "}
              {new Intl.DateTimeFormat(undefined, {
                dateStyle: "full",
                timeStyle: "short",
              }).format(new Date(entry.captured_at))}
            </p>
            {entry.notes && <p>📝 {entry.notes}</p>}
            {hasCoords && (
              <p>
                📍 {entry.latitude?.toFixed(5)}, {entry.longitude?.toFixed(5)}
              </p>
            )}
          </div>

          {mapUrl && (
            <div className="rounded-xl overflow-hidden border border-gray-200">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={mapUrl}
                alt="Map location"
                className="w-full"
                loading="lazy"
              />
            </div>
          )}

          <button
            onClick={onClose}
            className="w-full mt-2 border border-gray-300 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
