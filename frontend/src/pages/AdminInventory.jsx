import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import { getInventory } from "../services/inventoryApi";

export default function AdminInventory() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadInventory = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getInventory();

      setInventory(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load inventory.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, []);

  const lowStock = inventory.filter(
    (item) => item.stock_quantity <= item.reorder_threshold
  );

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">
              Inventory Management
            </h1>

            <p className="text-slate-500 mt-2">
              Monitor stock levels and inventory alerts.
            </p>
          </div>

          <button
            onClick={loadInventory}
            className="bg-slate-900 text-white px-5 py-3 rounded-lg font-semibold hover:bg-slate-800"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl border p-6">
            <p className="text-slate-500">Inventory Items</p>

            <p className="text-4xl font-bold text-slate-900 mt-2">
              {inventory.length}
            </p>
          </div>

          <div className="bg-white rounded-2xl border p-6">
            <p className="text-slate-500">Low Stock</p>

            <p className="text-4xl font-bold text-orange-600 mt-2">
              {lowStock.length}
            </p>
          </div>

          <div className="bg-white rounded-2xl border p-6">
            <p className="text-slate-500">Total Available Units</p>

            <p className="text-4xl font-bold text-green-600 mt-2">
              {inventory.reduce(
                (total, item) => total + Number(item.stock_quantity || 0),
                0
              )}
            </p>
          </div>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl border p-12 text-center text-slate-500">
            Loading inventory...
          </div>
        ) : (
          <div className="bg-white rounded-2xl border overflow-hidden">
            <div className="px-7 py-6 border-b border-slate-200">
              <h2 className="text-2xl font-bold text-slate-900">
                Stock Levels
              </h2>
            </div>

            {inventory.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                No inventory records found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="text-left px-7 py-5 text-sm font-semibold text-slate-600">
                        Product
                      </th>

                      <th className="text-left px-7 py-5 text-sm font-semibold text-slate-600">
                        Stock
                      </th>

                      <th className="text-left px-7 py-5 text-sm font-semibold text-slate-600">
                        Reserved
                      </th>

                      <th className="text-left px-7 py-5 text-sm font-semibold text-slate-600">
                        Reorder Level
                      </th>

                      <th className="text-left px-7 py-5 text-sm font-semibold text-slate-600">
                        Status
                      </th>

                      <th className="text-left px-7 py-5 text-sm font-semibold text-slate-600">
                        Updated
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {inventory.map((item) => {
                      const isLow =
                        Number(item.stock_quantity) <=
                        Number(item.reorder_threshold);

                      return (
                        <tr
                          key={item.product_id}
                          className="border-t border-slate-200"
                        >
                          <td className="px-7 py-6">
                            <p className="font-semibold text-slate-900">
                              {item.product_name}
                            </p>

                            <p className="text-xs text-slate-400 mt-1">
                              {item.product_id}
                            </p>
                          </td>

                          <td className="px-7 py-6 text-xl font-bold text-slate-900">
                            {item.stock_quantity}
                          </td>

                          <td className="px-7 py-6 text-slate-600">
                            {item.reserved_quantity}
                          </td>

                          <td className="px-7 py-6 text-slate-600">
                            {item.reorder_threshold}
                          </td>

                          <td className="px-7 py-6">
                            <span
                              className={
                                isLow
                                  ? "inline-flex px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700"
                                  : "inline-flex px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700"
                              }
                            >
                              {isLow ? "Low Stock" : "Healthy"}
                            </span>
                          </td>

                          <td className="px-7 py-6 text-sm text-slate-500">
                            {item.updated_at
                              ? new Date(item.updated_at).toLocaleString()
                              : "-"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
