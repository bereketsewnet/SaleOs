import { useState } from "react";
import { HiOutlineCube } from "react-icons/hi2";

export function ImageCarousel({ urls, alt }: { urls: string[]; alt: string }) {
  const [idx, setIdx] = useState(0);
  if (urls.length === 0) {
    return (
      <div className="aspect-square bg-tg-secondaryBg grid place-items-center text-tg-hint">
        <HiOutlineCube className="w-14 h-14" />
      </div>
    );
  }
  return (
    <div>
      <div className="aspect-square bg-tg-secondaryBg overflow-hidden">
        <img
          src={urls[idx]}
          alt={alt}
          className="w-full h-full object-cover animate-fade-in"
          key={idx}
        />
      </div>
      {urls.length > 1 && (
        <div className="flex gap-1.5 justify-center py-2.5">
          {urls.map((_, i) => (
            <button
              key={i}
              onClick={() => setIdx(i)}
              aria-label={`Image ${i + 1}`}
              className={`h-1.5 rounded-full transition-all ${
                i === idx ? "bg-brand-600 w-8" : "bg-slate-300 w-1.5 hover:bg-slate-400"
              }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
