import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { getProducts } from "../services/productApi";

export default function Products() {
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  const loadProducts = async (filters = {}) => {
    try {
      setLoading(true);
      setError("");

      const data = await getProducts(filters);

      setProducts(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load products.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();

    const filters = {};

    if (search.trim()) {
      filters.search = search.trim();
    }

    if (category.trim()) {
      filters.category = category.trim();
    }

    if (minPrice) {
      filters.minPrice = minPrice;
    }

    if (maxPrice) {
      filters.maxPrice = maxPrice;
    }

    loadProducts(filters);
  };

  const clearFilters = () => {
    setSearch("");
    setCategory("");
    setMinPrice("");
    setMaxPrice("");
    loadProducts();
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900">
            Product Catalogue
          </h1>

          <p className="mt-2 text-slate-500">
            Browse and purchase products from SmartRetailX.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8">
          <form
            onSubmit={handleSearch}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
          >
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border border-slate-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-slate-800"
            />

            <input
              type="text"
              placeholder="Category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="border border-slate-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-slate-800"
            />

            <input
              type="number"
              placeholder="Min price"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              className="border border-slate-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-slate-800"
            />

            <input
              type="number"
              placeholder="Max price"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              className="border border-slate-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-slate-800"
            />

            <button
              type="submit"
              className="bg-slate-900 text-white rounded-lg px-5 py-3 font-semibold hover:bg-slate-800"
            >
              Search
            </button>
          </form>

          <button
            onClick={clearFilters}
            className="mt-4 text-sm text-slate-500 hover:text-slate-900"
          >
            Clear filters
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-12 text-slate-500">
            Loading products...
          </div>
        )}

        {!loading && products.length === 0 && !error && (
          <div className="bg-white rounded-2xl border p-12 text-center">
            <h2 className="text-xl font-semibold text-slate-900">
              No products found
            </h2>

            <p className="text-slate-500 mt-2">
              Try changing your search filters.
            </p>
          </div>
        )}

        {!loading && products.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <div
                key={product.id}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition"
              >
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-52 object-cover"
                  />
                ) : (
                  <div className="w-full h-52 bg-slate-200 flex items-center justify-center text-slate-400">
                    No Image
                  </div>
                )}

                <div className="p-6">
                  <div className="flex justify-between items-start gap-4">
                    <h2 className="text-xl font-bold text-slate-900">
                      {product.name}
                    </h2>

                    <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-semibold">
                      {product.category}
                    </span>
                  </div>

                  <p className="mt-3 text-slate-500 line-clamp-3">
                    {product.description}
                  </p>

                  <div className="mt-6 flex justify-between items-center">
                    <span className="text-2xl font-bold text-slate-900">
                      LKR {Number(product.price).toFixed(2)}
                    </span>

                    <span
                      className={
                        product.stock_quantity > 0
                          ? "text-green-600 font-semibold"
                          : "text-red-600 font-semibold"
                      }
                    >
                      {product.stock_quantity > 0
                        ? `${product.stock_quantity} in stock`
                        : "Out of stock"}
                    </span>
                  </div>

                  <button
                    disabled={product.stock_quantity <= 0}
                    onClick={() =>
                      navigate(`/orders/new?productId=${product.id}`)
                    }
                    className="w-full mt-6 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white py-3 rounded-lg font-semibold transition"
                  >
                    {product.stock_quantity > 0 ? "Order Now" : "Out of Stock"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
