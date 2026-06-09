import { useState } from "react";
import { Link } from "react-router-dom";
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
    <div className="max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900">Products</h1>
          <p className="text-slate-500">Manage your catalog. Optionally publish each to your Telegram channel.</p>
        </div>
        {canEdit && (
          <Link
            to="/products/new"
            className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2.5"
          >
            + Add product
          </Link>
        )}
      </div>

      <div className="mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title…"
          className="w-full sm:max-w-sm rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
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
    <li className="bg-white border border-slate-200 rounded-2xl overflow-hidden flex flex-col">
      <div className="aspect-square bg-slate-100 flex items-center justify-center text-slate-300">
        {cover ? (
          <img src={cover} alt={product.title} className="w-full h-full object-cover" />
        ) : (
          <span className="text-4xl">📦</span>
        )}
      </div>
      <div className="p-4 flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold text-slate-900 line-clamp-2 flex-1">{product.title}</h3>
          <span className="font-semibold text-slate-900 whitespace-nowrap">
            {product.base_price ? `ETB ${product.base_price}` : "—"}
          </span>
        </div>
        <p className="text-xs text-slate-500 font-mono mb-2">SKU: {product.sku ?? "—"}</p>
        {!product.identifier && !product.instructions && !product.is_ocr_identified && (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5 mb-2 inline-block">
            ⚠ AI context not set
          </p>
        )}
        <p className="text-xs text-slate-600 mb-3">
          Stock:{" "}
          <span className={available > 0 ? "text-emerald-700 font-medium" : "text-red-700 font-medium"}>
            {available}
          </span>
          {product.reserved_quantity > 0 && (
            <span className="text-slate-500"> ({product.reserved_quantity} reserved)</span>
          )}
        </p>
        <div className="mt-auto flex flex-wrap gap-2">
          <Link
            to={`/products/${product.id}`}
            className="text-xs font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 px-3 py-1.5"
          >
            {canEdit ? "Edit" : "View"}
          </Link>
          {canEdit && (
            <>
              {product.is_published_to_channel ? (
                <span className="text-xs font-medium rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 px-3 py-1.5 flex items-center gap-1">
                  ✓ Published
                </span>
              ) : (
                <button
                  onClick={onPublish}
                  disabled={publishing}
                  className="text-xs font-medium rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 px-3 py-1.5 disabled:opacity-60"
                >
                  {publishing ? "Publishing…" : "Publish to channel"}
                </button>
              )}
              <button
                onClick={onDelete}
                className="text-xs font-medium rounded-lg border border-red-200 text-red-700 hover:bg-red-50 px-3 py-1.5"
              >
                Delete
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
    <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center">
      <p className="text-5xl mb-3">📦</p>
      <h3 className="text-lg font-semibold text-slate-900 mb-1">No products yet</h3>
      <p className="text-sm text-slate-500 mb-4">
        Add your first product to start selling on Telegram.
      </p>
      {canEdit && (
        <Link
          to="/products/new"
          className="inline-block rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2.5"
        >
          + Add product
        </Link>
      )}
    </div>
  );
}

function humanizeDeleteWarning(
  reason: string | null,
  failedCount: number
): string {
  const tail = `${failedCount} message${failedCount === 1 ? "" : "s"} could not be removed from your channel — delete them manually in Telegram.`;
  switch (reason) {
    case "missing_delete_permission":
      return `Product deleted from this panel, but the bot does NOT have "Delete messages" permission in your channel.\n\n${tail}\n\nFix: in Telegram, open your channel → Administrators → tap @your_bot → enable "Delete messages", then re-publish + re-delete next time.`;
    case "bot_not_running":
      return `Product deleted, but the bot wasn't running so channel messages weren't removed. ${tail}`;
    case "already_gone":
      // Treat as success silently — message was deleted in Telegram already.
      return `Product deleted. Some channel messages were already removed in Telegram.`;
    default:
      return `Product deleted, but ${tail}`;
  }
}
