"use client";

import { useState } from "react";
import Image from "next/image";
import type { WikiSummary } from "@/app/page";

interface Props {
  summary: WikiSummary | null;
}

export default function WikiPanel({ summary }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (summary === null) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-500">
        No Wikipedia article found for this species.
      </div>
    );
  }

  const articleUrl = summary.content_urls?.desktop?.page;

  return (
    <div className="rounded-xl border border-garden-200 bg-white p-4 shadow-sm space-y-3">
      <div className="flex gap-3">
        {summary.thumbnail && (
          <div className="flex-shrink-0">
            <Image
              src={summary.thumbnail.source}
              alt={summary.title}
              width={80}
              height={80}
              className="rounded-lg object-cover w-20 h-20"
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-garden-700">{summary.title}</p>
          {summary.description && (
            <p className="text-sm text-gray-600 mt-0.5">{summary.description}</p>
          )}
        </div>
      </div>

      {summary.extract && (
        <div>
          <p className={`text-sm text-gray-700 leading-relaxed ${!expanded ? "line-clamp-3" : ""}`}>
            {summary.extract}
          </p>
          {summary.extract.length > 200 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-garden-600 hover:underline mt-1"
            >
              {expanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}

      {articleUrl && (
        <a
          href={articleUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-garden-600 hover:underline font-medium"
        >
          Full Wikipedia article →
        </a>
      )}
    </div>
  );
}
