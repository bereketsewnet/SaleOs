import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
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
    <div>
      <header className="px-4 pt-4 pb-2 sticky top-0 z-10 bg-tg-bg">
        <h1 className="text-lg font-semibold">{info?.business_name ?? "Shop"}</h1>
        {info?.business_description && (
          <p className="text-xs text-tg-hint line-clamp-2">{info.business_description}</p>
        )}
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search…"
          className="mt-2 w-full rounded-xl bg-tg-secondaryBg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-tg-link/50"
        />
      </header>

      <div className="p-4">
        {isLoading ? (
          <p className="text-sm text-tg-hint">Loading…</p>
        ) : products.length === 0 ? (
          <p className="text-sm text-tg-hint text-center mt-12">No products yet.</p>
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
  return (
    <li>
      <Link
        to={withSearch(`/p/${product.id}`)}
        className="block rounded-2xl overflow-hidden bg-tg-secondaryBg active:opacity-70"
      >
        <div className="aspect-square bg-black/5 flex items-center justify-center">
          {product.image_url ? (
            <img src={product.image_url} alt={product.title} className="w-full h-full object-cover" />
          ) : (
            <span className="text-3xl">📦</span>
          )}
        </div>
        <div className="p-2">
          <p className="text-sm font-medium line-clamp-1">{product.title}</p>
          <p className="text-sm font-semibold mt-0.5">
            {product.base_price ? `ETB ${product.base_price}` : "Ask for price"}
          </p>
          {product.in_stock === 0 && (
            <p className="text-[10px] text-red-600 font-medium mt-0.5">Out of stock</p>
          )}
        </div>
      </Link>
    </li>
  );
}
