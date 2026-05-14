import type { Prediction } from "@/app/page";

interface Props {
  prediction: Prediction;
  rank: number;
}

export default function PlantCard({ prediction, rank }: Props) {
  const pct = Math.round(prediction.confidence * 100);

  return (
    <div className={`rounded-xl border p-4 shadow-sm ${rank === 0 ? "border-garden-400 bg-white" : "border-gray-200 bg-gray-50"}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className={`font-semibold ${rank === 0 ? "text-garden-700" : "text-gray-700"}`}>
            {prediction.common_name}
          </p>
          <p className="text-xs text-gray-500 italic">{prediction.species}</p>
        </div>
        <span className={`text-sm font-bold whitespace-nowrap ${rank === 0 ? "text-garden-700" : "text-gray-500"}`}>
          {pct}%
        </span>
      </div>
      <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${rank === 0 ? "bg-garden-500" : "bg-gray-400"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
