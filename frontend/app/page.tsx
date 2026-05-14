"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import CameraCapture from "@/components/CameraCapture";
import PlantCard from "@/components/PlantCard";
import WikiPanel from "@/components/WikiPanel";
import SaveButton from "@/components/SaveButton";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Prediction = {
  species: string;
  common_name: string;
  confidence: number;
};

export type WikiSummary = {
  title: string;
  description?: string;
  extract?: string;
  thumbnail?: { source: string; width: number; height: number };
  content_urls?: { desktop: { page: string } };
};

export default function Home() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [wiki, setWiki] = useState<WikiSummary | null | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);

  useEffect(() => {
    if (typeof navigator !== "undefined" && "geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => setCoords(null)
      );
    }
  }, []);

  const handleImage = useCallback((file: File) => {
    setImageFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setPredictions([]);
    setWiki(undefined);
    setError(null);
  }, []);

  async function identify() {
    if (!imageFile) return;
    setLoading(true);
    setError(null);
    setPredictions([]);
    setWiki(undefined);

    try {
      const form = new FormData();
      form.append("image", imageFile);

      const res = await fetch(`${API}/identify`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`Identification failed: ${res.status}`);
      const data = await res.json();
      const preds: Prediction[] = data.predictions ?? [];
      setPredictions(preds);

      if (preds.length > 0) {
        const top = preds[0];
        const wikiRes = await fetch(
          `${API}/wiki/${encodeURIComponent(top.species)}`
        );
        if (wikiRes.ok) {
          setWiki(await wikiRes.json());
        } else {
          setWiki(null);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-bold text-garden-700 mb-1">Identify a Plant</h1>
        <p className="text-sm text-gray-500">Take a photo or upload an image to identify the species.</p>
      </section>

      <CameraCapture onCapture={handleImage} />

      {previewUrl && (
        <div className="rounded-xl overflow-hidden border border-garden-100 shadow">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={previewUrl} alt="Plant preview" className="w-full object-cover max-h-72" />
        </div>
      )}

      {imageFile && (
        <button
          onClick={identify}
          disabled={loading}
          className="w-full bg-garden-600 hover:bg-garden-700 disabled:opacity-50 text-white font-semibold py-3 px-6 rounded-xl transition"
        >
          {loading ? "Identifying…" : "Identify Plant"}
        </button>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
          {error}
        </div>
      )}

      {predictions.length > 0 && (
        <section className="space-y-3">
          <h2 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">Results</h2>
          {predictions.map((p, i) => (
            <PlantCard key={i} prediction={p} rank={i} />
          ))}

          {wiki !== undefined && (
            <WikiPanel summary={wiki ?? null} />
          )}

          <SaveButton
            prediction={predictions[0]}
            imageFile={imageFile!}
            coords={coords}
            apiUrl={API}
          />
        </section>
      )}
    </div>
  );
}
