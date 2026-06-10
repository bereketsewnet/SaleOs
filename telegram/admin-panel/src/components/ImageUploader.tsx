import { useState, type ChangeEvent } from "react";
import { HiOutlinePhoto, HiOutlinePlus, HiOutlineXMark } from "react-icons/hi2";
import { uploadProductImage } from "../lib/productsApi";

interface Props {
  urls: string[];
  onChange: (urls: string[]) => void;
  max?: number;
  disabled?: boolean;
}

export function ImageUploader({ urls, onChange, max = 5, disabled }: Props) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFiles(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    setError(null);
    setUploading(true);
    try {
      const slots = max - urls.length;
      const toUpload = files.slice(0, slots);
      const uploaded = await Promise.all(toUpload.map((f) => uploadProductImage(f)));
      onChange([...urls, ...uploaded.map((u) => u.url)]);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail === "too_large"
          ? "Each image must be under 10 MB."
          : "Upload failed. Try again."
      );
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  function removeAt(idx: number) {
    onChange(urls.filter((_, i) => i !== idx));
  }

  return (
    <div>
      <div className="flex flex-wrap gap-3">
        {urls.map((u, idx) => (
          <div
            key={u + idx}
            className="relative w-28 h-28 rounded-2xl overflow-hidden ring-1 ring-slate-200 bg-slate-50 shadow-sm group"
          >
            <img src={u} alt="" className="w-full h-full object-cover" />
            {!disabled && (
              <button
                type="button"
                onClick={() => removeAt(idx)}
                className="absolute top-1.5 right-1.5 bg-slate-900/70 hover:bg-slate-900 text-white rounded-full w-6 h-6 grid place-items-center transition opacity-0 group-hover:opacity-100"
                aria-label="Remove image"
              >
                <HiOutlineXMark className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}

        {urls.length < max && !disabled && (
          <label className="w-28 h-28 rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50/50 flex flex-col items-center justify-center gap-1 text-xs text-slate-500 cursor-pointer hover:border-brand-500 hover:text-brand-700 hover:bg-brand-50/50 transition">
            {uploading ? (
              <span className="text-[11px]">Uploading…</span>
            ) : (
              <>
                <HiOutlinePlus className="w-5 h-5" />
                <span className="font-medium">Add image</span>
              </>
            )}
            <input
              type="file"
              accept="image/*"
              multiple
              className="sr-only"
              onChange={handleFiles}
              disabled={uploading}
            />
          </label>
        )}
      </div>
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
      <p className="mt-2 text-xs text-slate-500 flex items-center gap-1.5">
        <HiOutlinePhoto className="w-3.5 h-3.5" /> Up to {max} images · jpg / png / webp · max 10 MB each
      </p>
    </div>
  );
}
