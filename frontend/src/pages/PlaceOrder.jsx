import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { getProduct } from "../services/productApi";
import { createOrder } from "../services/orderApi";

export default function PlaceOrder() {
  const location = useLocation();
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);
  const productId = params.get("productId");

  const [product, setProduct] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [shippingAddress, setShippingAddress] = useState("");

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadProduct = async () => {
      if (!productId) {
        setError("No product selected.");
        setLoading(false);
        return;
      }

      try {
        const data = await getProduct(productId);
        setProduct(data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load product.");
      } finally {
        setLoading(false);
      }
    };

    loadProduct();
  }, [productId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!product) {
      return;
    }

    if (quantity < 1) {
      setError("Quantity must be at least 1.");
      return;
    }

    if (quantity > product.stock_quantity) {
      setError("Requested quantity exceeds available stock.");
      return;
    }

    if (!shippingAddress.trim()) {
      setError("Please enter a shipping address.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      await createOrder({
        product_id: product.id,
        quantity: Number(quantity),
        total_price: Number(product.price) * Number(quantity),
        shipping_address: shippingAddress.trim(),
      });

      navigate("/orders");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to place order.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100">
        <Navbar />
        <main className="max-w-5xl mx-auto px-6 py-12">
          <p className="text-slate-500">Loading product...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-5xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900">Place Order</h1>

          <p className="text-slate-500 mt-2">Complete your order details.</p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-red-700">
            {error}
          </div>
        )}

        {!product ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
            <h2 className="text-xl font-bold text-slate-900">
              Product not found
            </h2>

            <button
              onClick={() => navigate("/products")}
              className="mt-5 bg-slate-900 text-white px-5 py-3 rounded-lg font-semibold"
            >
              Back to Products
            </button>
          </div>
        ) : (
          <div className="grid lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-72 object-cover"
                />
              ) : (
                <div className="w-full h-72 bg-slate-200 flex items-center justify-center text-slate-400">
                  No Image
                </div>
              )}

              <div className="p-7">
                <span className="inline-flex bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-semibold">
                  {product.category}
                </span>

                <h2 className="text-3xl font-bold text-slate-900 mt-4">
                  {product.name}
                </h2>

                <p className="text-slate-500 mt-3">{product.description}</p>

                <div className="flex justify-between items-center mt-7">
                  <span className="text-3xl font-bold text-slate-900">
                    ${Number(product.price).toFixed(2)}
                  </span>

                  <span className="text-green-600 font-semibold">
                    {product.stock_quantity} available
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-8">
              <h2 className="text-2xl font-bold text-slate-900 mb-7">
                Order Details
              </h2>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Quantity
                  </label>

                  <input
                    type="number"
                    min="1"
                    max={product.stock_quantity}
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Shipping Address
                  </label>

                  <textarea
                    rows="5"
                    value={shippingAddress}
                    onChange={(e) => setShippingAddress(e.target.value)}
                    placeholder="Enter your delivery address"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-slate-800"
                    required
                  />
                </div>

                <div className="bg-slate-50 rounded-xl p-5">
                  <div className="flex justify-between text-slate-600">
                    <span>Unit Price</span>
                    <span>${Number(product.price).toFixed(2)}</span>
                  </div>

                  <div className="flex justify-between text-slate-600 mt-3">
                    <span>Quantity</span>
                    <span>{quantity}</span>
                  </div>

                  <div className="border-t border-slate-200 mt-4 pt-4 flex justify-between">
                    <span className="text-lg font-bold text-slate-900">
                      Total
                    </span>

                    <span className="text-2xl font-bold text-slate-900">
                      ${(Number(product.price) * Number(quantity)).toFixed(2)}
                    </span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white py-4 rounded-xl font-semibold"
                >
                  {submitting ? "Placing Order..." : "Place Order"}
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
