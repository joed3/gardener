"use client";

import { useRef, useState, useCallback } from "react";

interface Props {
  onCapture: (file: File) => void;
}

export default function CameraCapture({ onCapture }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
      }
    } catch {
      setCameraError("Camera not available. Please use the upload option.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    const video = videoRef.current;
    if (video?.srcObject) {
      (video.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
      video.srcObject = null;
    }
    setCameraActive(false);
  }, []);

  const capture = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
        onCapture(file);
        stopCamera();
      }
    }, "image/jpeg");
  }, [onCapture, stopCamera]);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onCapture(file);
    },
    [onCapture]
  );

  return (
    <div className="space-y-3">
      {cameraActive ? (
        <div className="space-y-2">
          <video
            ref={videoRef}
            className="w-full rounded-xl border border-garden-100 shadow"
            playsInline
            muted
          />
          <div className="flex gap-2">
            <button
              onClick={capture}
              className="flex-1 bg-garden-600 hover:bg-garden-700 text-white font-semibold py-2 rounded-xl transition"
            >
              📸 Capture
            </button>
            <button
              onClick={stopCamera}
              className="px-4 py-2 border border-gray-300 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <button
            onClick={startCamera}
            className="flex-1 flex items-center justify-center gap-2 bg-white border-2 border-garden-300 text-garden-700 font-semibold py-3 rounded-xl hover:bg-garden-50 transition"
          >
            📷 Use Camera
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 flex items-center justify-center gap-2 bg-white border-2 border-garden-300 text-garden-700 font-semibold py-3 rounded-xl hover:bg-garden-50 transition"
          >
            🖼 Upload Photo
          </button>
        </div>
      )}

      {cameraError && (
        <p className="text-sm text-amber-600 bg-amber-50 rounded-lg px-3 py-2">{cameraError}</p>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
