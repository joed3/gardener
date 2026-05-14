"use client";

import { useState } from "react";
import type { Prediction } from "@/app/page";

interface Props {
  prediction: Prediction;
  imageFile: File;
  coords: { lat: number; lon: number } | null;
  apiUrl: string;
}

export default function SaveButton({ prediction, imageFile, coords, apiUrl }: Props) {
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [notes, setNotes] = useState("");

  async function save() {
    setStatus("saving");
    try {
      // Upload image first
      const form = new FormData();
      form.append("image", imageFile);
      const uploadRes = await fetch(`${apiUrl}/garden/upload`, {
        method: "POST",
        body: form,
      });
      if (!uploadRes.ok) throw new Error("Image upload failed");
      const uploadData = await uploadRes.json();

      const capturedAt = uploadData.captured_at ?? new Date().toISOString();

      // Save garden entry
      const entryRes = await fetch(`${apiUrl}/garden`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          species: prediction.species,
          common_name: prediction.common_name,
          confidence: prediction.confidence,
          notes,
          captured_at: capturedAt,
          latitude: coords?.lat ?? null,
          longitude: coords?.lon ?? null,
        }),
      });
      if (!entryRes.ok) throw new Error("Failed to save entry");
      const entryData = await entryRes.json();

      // Attach image to entry
      await fetch(
        `${apiUrl}/garden/${entryData.id}/image?image_url=${encodeURIComponent(uploadData.image_url)}`,
        { method: "PATCH" }
      );

      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  if (status === "saved") {
    return (
      <div className="bg-garden-50 border border-garden-200 rounded-xl p-3 text-sm text-garden-700 font-medium">
        ✓ Saved to your garden!
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Add notes (optional)…"
        rows={2}
        className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-garden-400"
      />
      <button
        onClick={save}
        disabled={status === "saving"}
        className="w-full bg-garden-600 hover:bg-garden-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl transition text-sm"
      >
        {status === "saving" ? "Saving…" : "💾 Save to My Garden"}
      </button>
      {status === "error" && (
        <p className="text-xs text-red-600">Failed to save. Please try again.</p>
      )}
    </div>
  );
}
