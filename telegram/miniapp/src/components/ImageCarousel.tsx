import { useState } from "react";

export function ImageCarousel({ urls, alt }: { urls: string[]; alt: string }) {
  const [idx, setIdx] = useState(0);
  if (urls.length === 0) {
    return (
      <div className="aspect-square bg-black/5 flex items-center justify-center text-5xl">📦</div>
    );
  }
  return (
    <div>
      <div className="aspect-square bg-black/5">
        <img src={urls[idx]} alt={alt} className="w-full h-full object-cover" />
      </div>
      {urls.length > 1 && (
        <div className="flex gap-1 justify-center py-2">
          {urls.map((_, i) => (
            <button
              key={i}
              onClick={() => setIdx(i)}
              aria-label={`Image ${i + 1}`}
              className={`h-1.5 rounded-full transition-all ${
                i === idx ? "bg-tg-link w-6" : "bg-black/20 w-1.5"
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
