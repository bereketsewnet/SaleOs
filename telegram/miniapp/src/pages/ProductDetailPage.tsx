import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  HiOutlineArrowLeft,
  HiOutlineChatBubbleLeftRight,
  HiOutlineShoppingCart,
  HiOutlineBolt,
  HiOutlineCheckCircle,
} from "react-icons/hi2";
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

  if (isLoading) return <p className="p-6 text-tg-hint">Loading…</p>;
  if (!product) return <p className="p-6 text-tg-hint">Product not found.</p>;

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

  const oos = product.in_stock === 0;

  return (
    <div className="pb-32 animate-fade-in">
      {/* Back button overlay */}
      <Link
        to={withSearch("/")}
        className="absolute top-3 left-3 z-10 w-10 h-10 rounded-full bg-white/80 backdrop-blur grid place-items-center text-slate-700 shadow-sm active:scale-95"
      >
        <HiOutlineArrowLeft className="w-5 h-5" />
      </Link>

      <ImageCarousel urls={product.image_urls} alt={product.title} />

      <div className="px-4 pt-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-tg-text leading-tight">{product.title}</h1>
            {oos ? (
              <span className="chip bg-red-100 text-red-700 mt-2">Sold out</span>
            ) : (
              <span className="chip bg-emerald-100 text-emerald-700 mt-2">
                <HiOutlineCheckCircle className="w-3.5 h-3.5" /> {product.in_stock} in stock
              </span>
            )}
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-brand-700 leading-none">
              {product.base_price ? `ETB ${product.base_price}` : "Ask"}
            </p>
          </div>
        </div>

        {product.description && (
          <div className="card card-pad mt-2 animate-slide-up">
            <p className="text-xs uppercase tracking-wider text-tg-hint font-semibold mb-1.5">
              About
            </p>
            <p className="text-sm whitespace-pre-wrap text-tg-text leading-relaxed">
              {product.description}
            </p>
          </div>
        )}
      </div>

      {/* Sticky bottom actions */}
      <div className="fixed bottom-[68px] inset-x-0 z-30 px-4 py-3 bg-tg-bg/95 backdrop-blur-xl border-t border-black/5">
        <div className="grid grid-cols-3 gap-2 max-w-md mx-auto">
          <button
            onClick={() => setChatOpen(true)}
            className="btn-secondary py-3 text-xs sm:text-sm"
          >
            <HiOutlineChatBubbleLeftRight className="w-4 h-4" /> Ask
          </button>
          <button
            onClick={addToCart}
            disabled={oos}
            className="btn-secondary py-3 text-xs sm:text-sm"
          >
            <HiOutlineShoppingCart className="w-4 h-4" /> Cart
          </button>
          <button onClick={buyNow} disabled={oos} className="btn-primary py-3 text-xs sm:text-sm">
            <HiOutlineBolt className="w-4 h-4" /> Buy now
          </button>
        </div>
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
