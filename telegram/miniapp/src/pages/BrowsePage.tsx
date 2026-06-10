import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  HiOutlineMagnifyingGlass,
  HiOutlineCube,
  HiOutlineSparkles,
} from "react-icons/hi2";
import { listProducts, type CatalogProduct } from "../lib/catalogApi";
import { getMerchantInfo } from "../lib/catalogApi";
import { withSearch } from "../lib/nav";

export default function BrowsePage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["products", search],
    queryFn: () => listProducts(search || undefined),
  });
  const products = Array.isArray(data) ? data : [];
  const { data: info } = useQuery({
    queryKey: ["merchantInfo"],
    queryFn: getMerchantInfo,
  });

  return (
    <div className="pb-24 animate-fade-in">
      <header className="px-4 pt-5 pb-3 sticky top-0 z-20 bg-tg-bg/90 backdrop-blur-xl border-b border-black/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 grid place-items-center text-white shadow-sm shrink-0">
            <HiOutlineSparkles className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-base font-bold text-tg-text truncate">
              {info?.business_name ?? "Shop"}
            </h1>
            {info?.business_description && (
              <p className="text-xs text-tg-hint line-clamp-1">{info.business_description}</p>
            )}
          </div>
        </div>

        <div className="relative mt-3">
          <HiOutlineMagnifyingGlass className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search products…"
            className="input pl-10"
          />
        </div>
      </header>

      <div className="px-4 pt-4">
        {isLoading ? (
          <SkeletonGrid />
        ) : products.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {products.map((p) => (
              <Card key={p.id} product={p} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Card({ product }: { product: CatalogProduct }) {
  const oos = product.in_stock === 0;
  return (
    <li className="animate-slide-up">
      <Link
        to={withSearch(`/p/${product.id}`)}
        className="card overflow-hidden block active:scale-[0.98] transition"
      >
        <div className="aspect-square bg-tg-secondaryBg grid place-items-center relative overflow-hidden">
          {product.image_url ? (
            <img src={product.image_url} alt={product.title} className="w-full h-full object-cover" />
          ) : (
            <HiOutlineCube className="w-10 h-10 text-tg-hint" />
          )}
          {oos && (
            <span className="absolute top-2 left-2 chip bg-red-500 text-white">
              Sold out
            </span>
          )}
        </div>
        <div className="p-3">
          <p className="text-sm font-semibold text-tg-text line-clamp-1">{product.title}</p>
          <p className="text-sm font-bold text-brand-700 mt-1">
            {product.base_price ? `ETB ${product.base_price}` : "Ask price"}
          </p>
        </div>
      </Link>
    </li>
  );
}

function SkeletonGrid() {
  return (
    <ul className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <li key={i} className="card overflow-hidden animate-pulse">
          <div className="aspect-square bg-slate-200" />
          <div className="p-3 space-y-2">
            <div className="h-3 bg-slate-200 rounded w-3/4" />
            <div className="h-3 bg-slate-200 rounded w-1/2" />
          </div>
        </li>
      ))}
    </ul>
  );
}

function EmptyState() {
  return (
    <div className="card card-pad p-10 text-center mt-6">
      <div className="w-14 h-14 rounded-2xl bg-brand-50 grid place-items-center text-brand-600 mx-auto mb-3">
        <HiOutlineCube className="w-7 h-7" />
      </div>
      <p className="text-sm font-semibold text-tg-text">No products yet</p>
      <p className="text-xs text-tg-hint mt-1">Check back soon.</p>
    </div>
  );
}
