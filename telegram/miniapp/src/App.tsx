import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { BottomNav } from "./components/BottomNav";
import { getMerchantInfo } from "./lib/catalogApi";
import { getMerchantId } from "./lib/telegram";
import BrowsePage from "./pages/BrowsePage";
import ProductDetailPage from "./pages/ProductDetailPage";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import OrderSuccessPage from "./pages/OrderSuccessPage";
import InfoPage from "./pages/InfoPage";

export default function App() {
  const merchantId = getMerchantId();

  // Pre-warm merchant-info so InfoPage and OrderSuccess render instantly.
  useQuery({
    queryKey: ["merchantInfo"],
    queryFn: getMerchantInfo,
    enabled: !!merchantId,
  });

  useEffect(() => {
    document.title = "Shop";
  }, []);

  if (!merchantId) {
    return (
      <div className="p-6 text-center">
        <h1 className="text-xl font-semibold">Shop link is incomplete</h1>
        <p className="text-sm text-tg-hint mt-2">
          The Mini App needs a <code>merchant_id</code> in the URL or as the
          Telegram start parameter (<code>start=merchant_&lt;uuid&gt;</code>).
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-full pb-16">
      <Routes>
        <Route path="/" element={<BrowsePage />} />
        <Route path="/p/:productId" element={<ProductDetailPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/order/:orderId/success" element={<OrderSuccessPage />} />
        <Route path="/info" element={<InfoPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <BottomNav />
    </div>
  );
}
