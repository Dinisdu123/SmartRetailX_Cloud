import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct,
} from "../services/productApi";

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    category: "",
    stock_quantity: "",
    image_url: "",
  });

  // Load products
  const loadProducts = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getProducts();
      setProducts(data);
    } catch (err) {
      console.error("Failed to load products:", err);

      setError(err.response?.data?.detail || "Failed to load products.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  // Handle form input
  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Reset form
  const resetForm = () => {
    setForm({
      name: "",
      description: "",
      price: "",
      category: "",
      stock_quantity: "",
      image_url: "",
    });

    setEditingId(null);
    setShowForm(false);
  };

  // Add product
  const handleAdd = () => {
    setEditingId(null);

    setForm({
      name: "",
      description: "",
      price: "",
      category: "",
      stock_quantity: "",
      image_url: "",
    });

    setShowForm(true);
    setError("");
  };

  // Edit product
  const handleEdit = (product) => {
    setEditingId(product.id);

    setForm({
      name: product.name || "",
      description: product.description || "",
      price: product.price || "",
      category: product.category || "",
      stock_quantity: product.stock_quantity || "",
      image_url: product.image_url || "",
    });

    setShowForm(true);
    setError("");
  };

  // Submit product
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setError("");

      const productData = {
        name: form.name,
        description: form.description,
        price: Number(form.price),
        category: form.category,
        stock_quantity: Number(form.stock_quantity),
        image_url: form.image_url || null,
      };

      if (editingId) {
        await updateProduct(editingId, productData);
      } else {
        await createProduct(productData);
      }

      await loadProducts();
      resetForm();
    } catch (err) {
      console.error("Failed to save product:", err);

      setError(err.response?.data?.detail || "Failed to save product.");
    }
  };

  // Delete product
  const handleDelete = async (productId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this product?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await deleteProduct(productId);

      await loadProducts();
    } catch (err) {
      console.error("Failed to delete product:", err);

      setError(err.response?.data?.detail || "Failed to delete product.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Navigation Bar */}
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">
              Product Management
            </h1>

            <p className="mt-2 text-slate-500">
              Create, update and manage SmartRetailX products.
            </p>
          </div>

          <button
            onClick={handleAdd}
            className="bg-slate-900 text-white px-6 py-4 rounded-lg font-semibold hover:bg-slate-800 transition"
          >
            + Add Product
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        {/* Add/Edit Form */}
        {showForm && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-slate-900">
                {editingId ? "Edit Product" : "Add Product"}
              </h2>

              <button
                onClick={resetForm}
                className="text-slate-500 hover:text-slate-900 text-xl"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Name */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Product Name
                  </label>

                  <input
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    required
                    minLength={2}
                    maxLength={100}
                    placeholder="Enter product name"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Category
                  </label>

                  <input
                    type="text"
                    name="category"
                    value={form.category}
                    onChange={handleChange}
                    required
                    maxLength={50}
                    placeholder="e.g. Electronics"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>

                {/* Price */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Price
                  </label>

                  <input
                    type="number"
                    name="price"
                    value={form.price}
                    onChange={handleChange}
                    required
                    min="0.01"
                    step="0.01"
                    placeholder="Enter price"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>

                {/* Stock */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Stock Quantity
                  </label>

                  <input
                    type="number"
                    name="stock_quantity"
                    value={form.stock_quantity}
                    onChange={handleChange}
                    required
                    min="0"
                    step="1"
                    placeholder="Enter stock quantity"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>

                {/* Image URL */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Image URL
                  </label>

                  <input
                    type="text"
                    name="image_url"
                    value={form.image_url}
                    onChange={handleChange}
                    placeholder="https://example.com/image.jpg"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>

                {/* Description */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Description
                  </label>

                  <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    required
                    maxLength={1000}
                    rows={4}
                    placeholder="Enter product description"
                    className="w-full border border-slate-300 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>
              </div>

              {/* Form Buttons */}
              <div className="flex gap-4 mt-6">
                <button
                  type="submit"
                  className="bg-slate-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-slate-800 transition"
                >
                  {editingId ? "Update Product" : "Create Product"}
                </button>

                <button
                  type="button"
                  onClick={resetForm}
                  className="bg-slate-200 text-slate-700 px-6 py-3 rounded-lg font-semibold hover:bg-slate-300 transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Products Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Table Header */}
          <div className="px-7 py-6 border-b border-slate-200">
            <h2 className="text-2xl font-bold text-slate-900">Products</h2>

            <p className="text-slate-500 mt-1">
              {products.length} {products.length === 1 ? "product" : "products"}{" "}
              in catalogue
            </p>
          </div>

          {/* Loading */}
          {loading && (
            <div className="text-center py-12 text-slate-500">
              Loading products...
            </div>
          )}

          {/* Empty */}
          {!loading && products.length === 0 && !error && (
            <div className="text-center py-12">
              <h3 className="text-xl font-semibold text-slate-900">
                No products found
              </h3>

              <p className="text-slate-500 mt-2">
                Add your first product to the catalogue.
              </p>
            </div>
          )}

          {/* Table */}
          {!loading && products.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-7 py-4 text-sm font-semibold text-slate-700">
                      Product
                    </th>

                    <th className="text-left px-7 py-4 text-sm font-semibold text-slate-700">
                      Category
                    </th>

                    <th className="text-left px-7 py-4 text-sm font-semibold text-slate-700">
                      Price
                    </th>

                    <th className="text-left px-7 py-4 text-sm font-semibold text-slate-700">
                      Stock
                    </th>

                    <th className="text-right px-7 py-4 text-sm font-semibold text-slate-700">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {products.map((product) => (
                    <tr
                      key={product.id}
                      className="border-b border-slate-200 last:border-b-0"
                    >
                      {/* Product */}
                      <td className="px-7 py-5">
                        <div className="flex items-center gap-4">
                          {product.image_url ? (
                            <img
                              src={product.image_url}
                              alt={product.name}
                              className="w-16 h-16 rounded-lg object-cover bg-slate-100"
                            />
                          ) : (
                            <div className="w-16 h-16 rounded-lg bg-slate-200 flex items-center justify-center text-xs text-slate-400">
                              No Image
                            </div>
                          )}

                          <div>
                            <p className="font-semibold text-slate-900">
                              {product.name}
                            </p>

                            <p className="text-slate-500 text-sm mt-1">
                              {product.description}
                            </p>
                          </div>
                        </div>
                      </td>

                      {/* Category */}
                      <td className="px-7 py-5">
                        <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                          {product.category}
                        </span>
                      </td>

                      {/* Price */}
                      <td className="px-7 py-5">
                        <span className="font-semibold text-slate-900">
                          LKR {Number(product.price).toFixed(2)}
                        </span>
                      </td>

                      {/* Stock */}
                      <td className="px-7 py-5">
                        <span
                          className={
                            product.stock_quantity > 0
                              ? "text-green-600 font-semibold"
                              : "text-red-600 font-semibold"
                          }
                        >
                          {product.stock_quantity}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-7 py-5">
                        <div className="flex justify-end gap-3">
                          <button
                            onClick={() => handleEdit(product)}
                            className="bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-blue-100 transition"
                          >
                            Edit
                          </button>

                          <button
                            onClick={() => handleDelete(product.id)}
                            className="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-medium hover:bg-red-100 transition"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
