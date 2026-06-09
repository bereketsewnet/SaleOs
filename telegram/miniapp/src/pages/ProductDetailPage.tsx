import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getProduct } from "../lib/catalogApi";
import { useCart } from "../store/cart";
import { ImageCarousel } from "../components/ImageCarousel";
import { ChatPanel } from "../components/ChatPanel";
import { hapticImpact } from "../lib/telegram";
import { withSearch } from "../lib/nav";

export default function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const [chatOpen, setChatOpen] = useState(false);
  const addItem = useCart((s) => s.addItem);

  const { data: product, isLoading } = useQuery({
    queryKey: ["product", productId],
    queryFn: () => getProduct(productId!),
    enabled: !!productId,
  });

  if (isLoading) return <p className="p-4 text-tg-hint">Loading…</p>;
  if (!product) return <p className="p-4 text-tg-hint">Product not found.</p>;

  function addToCart() {
    if (!product) return;
    addItem(
      {
        product_id: product.id,
        title: product.title,
        base_price: product.base_price ?? "0",
        image_url: product.image_url,
      },
      1
    );
    hapticImpact("light");
  }

  function buyNow() {
    addToCart();
    navigate(withSearch("/cart"));
  }

  return (
    <div>
      <div className="px-3 py-2">
        <Link to={withSearch("/")} className="text-tg-link text-sm">
          ← Back
        </Link>
      </div>
      <ImageCarousel urls={product.image_urls} alt={product.title} />
      <div className="px-4 py-3">
        <h1 className="text-xl font-semibold">{product.title}</h1>
        <p className="text-2xl font-bold mt-1">
          {product.base_price ? `ETB ${product.base_price}` : "Ask for price"}
        </p>
        {product.in_stock === 0 ? (
          <p className="text-sm text-red-600 mt-1">Out of stock</p>
        ) : (
          <p className="text-xs text-tg-hint mt-1">{product.in_stock} in stock</p>
        )}
        {product.description && (
          <p className="text-sm mt-3 whitespace-pre-wrap">{product.description}</p>
        )}
      </div>

      {/* Sticky bottom actions */}
      <div className="fixed bottom-16 inset-x-0 px-4 py-3 bg-tg-bg border-t border-black/10 grid grid-cols-3 gap-2">
        <button
          onClick={() => setChatOpen(true)}
          className="py-3 rounded-xl bg-tg-secondaryBg text-sm font-medium"
        >
          💬 Ask
        </button>
        <button
          onClick={addToCart}
          disabled={product.in_stock === 0}
          className="py-3 rounded-xl bg-tg-secondaryBg text-sm font-medium disabled:opacity-50"
        >
          + Cart
        </button>
        <button
          onClick={buyNow}
          disabled={product.in_stock === 0}
          className="py-3 rounded-xl bg-tg-button text-tg-buttonText text-sm font-semibold disabled:opacity-50"
        >
          Buy now
        </button>
      </div>

      {chatOpen && (
        <ChatPanel
          productId={product.id}
          onClose={() => setChatOpen(false)}
          onAddToCart={addToCart}
        />
      )}
    </div>
  );
}
