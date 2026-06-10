import { useState } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineCube,
  HiOutlinePlus,
  HiOutlineMagnifyingGlass,
  HiOutlineExclamationTriangle,
  HiOutlineCheckCircle,
  HiOutlinePencilSquare,
  HiOutlineTrash,
  HiOutlinePaperAirplane,
} from "react-icons/hi2";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteProduct,
  listProducts,
  publishProductToChannel,
  type Product,
} from "../lib/productsApi";
import { useHasRole } from "../components/RoleGate";

export default function ProductsPage() {
  const canEdit = useHasRole(["ADMIN"]);
  const [search, setSearch] = useState("");
  const qc = useQueryClient();

  const { data: products = [], isLoading } = useQuery({
    queryKey: ["products", search],
    queryFn: () => listProducts(search || undefined),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: (summary) => {
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["channelPosts"] });
      if (summary.channel_messages_failed > 0) {
        alert(humanizeDeleteWarning(summary.channel_reason, summary.channel_messages_failed));
      }
    },
  });

  const publishMutation = useMutation({
    mutationFn: publishProductToChannel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["channelPosts"] });
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });

  return (
    <div className="max-w-6xl mx-auto space-y-5 animate-fade-in">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Products</h1>
          <p className="text-slate-500 text-sm mt-1">
            Manage your catalog. Publish to your Telegram channel with one tap.
          </p>
        </div>
        {canEdit && (
          <Link to="/products/new" className="btn-primary">
            <HiOutlinePlus className="w-4 h-4" />
            Add product
          </Link>
        )}
      </div>

      <div className="relative max-w-md">
        <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search products…"
          className="input pl-9"
        />
      </div>

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : products.length === 0 ? (
        <EmptyState canEdit={canEdit} />
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              canEdit={canEdit}
              onDelete={() => {
                if (confirm(`Delete "${p.title}"? This can't be undone.`)) {
                  deleteMutation.mutate(p.id);
                }
              }}
              onPublish={() => publishMutation.mutate(p.id)}
              publishing={publishMutation.isPending && publishMutation.variables === p.id}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function ProductCard({
  product,
  canEdit,
  onDelete,
  onPublish,
  publishing,
}: {
  product: Product;
  canEdit: boolean;
  onDelete: () => void;
  onPublish: () => void;
  publishing: boolean;
}) {
  const cover = product.image_urls[0];
  const available = product.quantity - product.reserved_quantity;
  return (
    <li className="card overflow-hidden flex flex-col group">
      <div className="aspect-square bg-slate-100 flex items-center justify-center text-slate-300 relative">
        {cover ? (
          <img
            src={cover}
            alt={product.title}
            className="w-full h-full object-cover transition group-hover:scale-105"
          />
        ) : (
          <HiOutlineCube className="w-14 h-14" />
        )}
        {product.is_published_to_channel && (
          <span className="absolute top-2 right-2 badge bg-emerald-100 text-emerald-700 backdrop-blur shadow-sm">
            <HiOutlineCheckCircle className="w-3.5 h-3.5" /> Live
          </span>
        )}
      </div>
      <div className="p-4 flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold text-slate-900 line-clamp-2 flex-1 leading-tight">
            {product.title}
          </h3>
          <span className="font-bold text-slate-900 whitespace-nowrap">
            {product.base_price ? `ETB ${product.base_price}` : "—"}
          </span>
        </div>
        <p className="text-xs text-slate-400 font-mono mb-2">SKU: {product.sku ?? "—"}</p>
        {!product.identifier && !product.instructions && !product.is_ocr_identified && (
          <p className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5 mb-2 w-fit">
            <HiOutlineExclamationTriangle className="w-3 h-3" /> AI context not set
          </p>
        )}
        <p className="text-xs text-slate-600 mb-3">
          Stock:{" "}
          <span className={available > 0 ? "text-emerald-700 font-semibold" : "text-red-700 font-semibold"}>
            {available}
          </span>
          {product.reserved_quantity > 0 && (
            <span className="text-slate-400 ml-1">({product.reserved_quantity} reserved)</span>
          )}
        </p>
        <div className="mt-auto flex flex-wrap gap-2">
          <Link
            to={`/products/${product.id}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 transition"
          >
            <HiOutlinePencilSquare className="w-3.5 h-3.5" /> {canEdit ? "Edit" : "View"}
          </Link>
          {canEdit && (
            <>
              {!product.is_published_to_channel && (
                <button
                  onClick={onPublish}
                  disabled={publishing}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 px-3 py-1.5 disabled:opacity-60 transition"
                >
                  <HiOutlinePaperAirplane className="w-3.5 h-3.5" />
                  {publishing ? "Publishing…" : "Publish"}
                </button>
              )}
              <button
                onClick={onDelete}
                className="inline-flex items-center gap-1.5 text-xs font-semibold rounded-lg bg-red-50 hover:bg-red-100 text-red-700 px-3 py-1.5 transition"
              >
                <HiOutlineTrash className="w-3.5 h-3.5" /> Delete
              </button>
            </>
          )}
        </div>
      </div>
    </li>
  );
}

function EmptyState({ canEdit }: { canEdit: boolean }) {
  return (
    <div className="card card-pad p-10 text-center">
      <div className="w-16 h-16 rounded-2xl bg-brand-50 grid place-items-center text-brand-600 mx-auto mb-4">
        <HiOutlineCube className="w-9 h-9" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-1">No products yet</h3>
      <p className="text-sm text-slate-500 mb-5 max-w-sm mx-auto">
        Add your first product to start selling. Or send a #product post in your Telegram
        channel and the bot will create it for you.
      </p>
      {canEdit && (
        <Link to="/products/new" className="btn-primary inline-flex">
          <HiOutlinePlus className="w-4 h-4" /> Add product
        </Link>
      )}
    </div>
  );
}

function humanizeDeleteWarning(reason: string | null, failedCount: number): string {
  const tail = `${failedCount} message${failedCount === 1 ? "" : "s"} could not be removed from your channel — delete them manually in Telegram.`;
  switch (reason) {
    case "missing_delete_permission":
      return `Product deleted from this panel, but the bot does NOT have "Delete messages" permission in your channel.\n\n${tail}\n\nFix: in Telegram, open your channel → Administrators → tap @your_bot → enable "Delete messages".`;
    case "bot_not_running":
      return `Product deleted, but the bot wasn't running so channel messages weren't removed. ${tail}`;
    case "already_gone":
      return `Product deleted. Some channel messages were already removed in Telegram.`;
    default:
      return `Product deleted, but ${tail}`;
  }
}
