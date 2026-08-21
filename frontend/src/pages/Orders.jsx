import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import { useAuth } from "../context/AuthContext";

import { getOrders, updateOrderStatus } from "../services/orderApi";

import { getProducts } from "../services/productApi";
import { getUsers } from "../services/UserApi";

const statuses = ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"];

export default function Orders() {
  const { user } = useAuth();

  const [orders, setOrders] = useState([]);

  const [products, setProducts] = useState([]);
  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [updatingId, setUpdatingId] = useState(null);

  // ============================================================
  // LOAD ORDERS + PRODUCTS + USERS
  // ============================================================

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError("");

      const ordersData = await getOrders();

      setOrders(ordersData);

      // --------------------------------------------------------
      // Load products
      // --------------------------------------------------------

      try {
        const productsData = await getProducts();

        setProducts(productsData);
      } catch (productError) {
        console.error("Failed to load products:", productError);
      }

      // --------------------------------------------------------
      // Load users only for admin
      // --------------------------------------------------------

      if (user?.role === "admin") {
        try {
          const usersData = await getUsers();

          setUsers(usersData);
        } catch (userError) {
          console.error("Failed to load users:", userError);
        }
      }
    } catch (err) {
      console.error("Failed to load orders:", err);

      setError(err.response?.data?.detail || "Failed to load orders.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadOrders();
    }
  }, [user]);

  // ============================================================
  // FIND PRODUCT NAME
  // ============================================================

  const getProductName = (productId) => {
    const product = products.find(
      (item) => String(item.id) === String(productId)
    );

    return product?.name || "Unknown Product";
  };

  // ============================================================
  // FIND CUSTOMER NAME
  // ============================================================

  const getCustomerName = (userId) => {
    const customer = users.find((item) => String(item.id) === String(userId));

    return customer?.name || "Unknown Customer";
  };

  // ============================================================
  // UPDATE STATUS
  // ============================================================

  const handleStatusChange = async (orderId, status) => {
    try {
      setUpdatingId(orderId);
      setError("");

      const updated = await updateOrderStatus(orderId, status);

      setOrders((current) =>
        current.map((order) =>
          String(order.id) === String(orderId) ? updated : order
        )
      );
    } catch (err) {
      console.error("Failed to update order:", err);

      setError(err.response?.data?.detail || "Failed to update order status.");
    } finally {
      setUpdatingId(null);
    }
  };

  // ============================================================
  // STATUS STYLE
  // ============================================================

  const getStatusClass = (status) => {
    const styles = {
      PENDING: "bg-yellow-100 text-yellow-700",

      CONFIRMED: "bg-blue-100 text-blue-700",

      SHIPPED: "bg-indigo-100 text-indigo-700",

      DELIVERED: "bg-green-100 text-green-700",

      CANCELLED: "bg-red-100 text-red-700",
    };

    return styles[status] || "bg-slate-100 text-slate-700";
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        {/* ================================================== */}
        {/* HEADER */}
        {/* ================================================== */}

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900">
            {user?.role === "admin" ? "Order Management" : "My Orders"}
          </h1>

          <p className="text-slate-500 mt-2">
            {user?.role === "admin"
              ? "Monitor and manage SmartRetailX orders."
              : "View your SmartRetailX order history."}
          </p>
        </div>

        {/* ================================================== */}
        {/* ERROR */}
        {/* ================================================== */}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6">
            {error}
          </div>
        )}

        {/* ================================================== */}
        {/* SUMMARY CARDS */}
        {/* ================================================== */}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-5 mb-8">
          {/* TOTAL */}

          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-slate-500">Total Orders</p>

            <p className="text-3xl font-bold mt-2">{orders.length}</p>
          </div>

          {/* PENDING */}

          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-slate-500">Pending</p>

            <p className="text-3xl font-bold text-yellow-600 mt-2">
              {orders.filter((o) => o.status === "PENDING").length}
            </p>
          </div>

          {/* CONFIRMED */}

          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-slate-500">Confirmed</p>

            <p className="text-3xl font-bold text-blue-600 mt-2">
              {orders.filter((o) => o.status === "CONFIRMED").length}
            </p>
          </div>

          {/* DELIVERED */}

          <div className="bg-white rounded-xl border p-5">
            <p className="text-sm text-slate-500">Delivered</p>

            <p className="text-3xl font-bold text-green-600 mt-2">
              {orders.filter((o) => o.status === "DELIVERED").length}
            </p>
          </div>
        </div>

        {/* ================================================== */}
        {/* LOADING */}
        {/* ================================================== */}

        {loading ? (
          <div className="bg-white rounded-2xl border p-12 text-center text-slate-500">
            Loading orders...
          </div>
        ) : orders.length === 0 ? (
          /* ================================================== */
          /* NO ORDERS */
          /* ================================================== */

          <div className="bg-white rounded-2xl border p-12 text-center">
            <h2 className="text-xl font-bold text-slate-900">
              No orders found
            </h2>

            <p className="text-slate-500 mt-2">
              {user?.role === "admin"
                ? "There are currently no orders."
                : "You have not placed any orders yet."}
            </p>
          </div>
        ) : (
          /* ================================================== */
          /* ORDER TABLE */
          /* ================================================== */

          <div className="bg-white rounded-2xl border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                      Order
                    </th>

                    {user?.role === "admin" && (
                      <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                        Customer
                      </th>
                    )}

                    <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                      Product
                    </th>

                    <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                      Shipping Address
                    </th>

                    <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                      Quantity
                    </th>

                    <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                      Total
                    </th>

                    <th className="text-left px-6 py-5 text-sm font-semibold text-slate-600">
                      Status
                    </th>

                    {user?.role === "admin" && (
                      <th className="text-right px-6 py-5 text-sm font-semibold text-slate-600">
                        Update
                      </th>
                    )}
                  </tr>
                </thead>

                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id} className="border-t border-slate-200">
                      {/* ================================== */}
                      {/* ORDER */}
                      {/* ================================== */}

                      <td className="px-6 py-6">
                        <p className="font-semibold text-slate-900">
                          #{String(order.id).slice(0, 8)}
                        </p>

                        <p className="text-xs text-slate-400 mt-1">
                          {order.created_at
                            ? new Date(order.created_at).toLocaleString()
                            : "-"}
                        </p>
                      </td>

                      {/* ================================== */}
                      {/* CUSTOMER */}
                      {/* ================================== */}

                      {user?.role === "admin" && (
                        <td className="px-6 py-6">
                          <p className="font-semibold text-slate-900">
                            {getCustomerName(order.user_id)}
                          </p>

                          <p className="text-xs text-slate-400 mt-1">
                            {String(order.user_id).slice(0, 8)}
                          </p>
                        </td>
                      )}

                      {/* ================================== */}
                      {/* PRODUCT */}
                      {/* ================================== */}

                      <td className="px-6 py-6">
                        <p className="font-semibold text-slate-900">
                          {getProductName(order.product_id)}
                        </p>

                        <p className="text-xs text-slate-400 mt-1">
                          {String(order.product_id).slice(0, 8)}
                        </p>
                      </td>

                      <td className="px-6 py-6 text-sm text-slate-600 max-w-xs">
                        <p className="break-words">
                          {order.shipping_address || "No address provided"}
                        </p>
                      </td>

                      {/* ================================== */}
                      {/* QUANTITY */}
                      {/* ================================== */}

                      <td className="px-6 py-6 text-slate-700">
                        {order.quantity}
                      </td>

                      {/* ================================== */}
                      {/* TOTAL */}
                      {/* ================================== */}

                      <td className="px-6 py-6 font-semibold text-slate-900">
                        LKR {Number(order.total_price).toFixed(2)}
                      </td>

                      {/* ================================== */}
                      {/* STATUS */}
                      {/* ================================== */}

                      <td className="px-6 py-6">
                        <span
                          className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${getStatusClass(
                            order.status
                          )}`}
                        >
                          {order.status}
                        </span>
                      </td>

                      {/* ================================== */}
                      {/* UPDATE */}
                      {/* ================================== */}

                      {user?.role === "admin" && (
                        <td className="px-6 py-6 text-right">
                          <select
                            value={order.status}
                            disabled={updatingId === order.id}
                            onChange={(e) =>
                              handleStatusChange(order.id, e.target.value)
                            }
                            className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-800"
                          >
                            {statuses.map((status) => (
                              <option key={status} value={status}>
                                {status}
                              </option>
                            ))}
                          </select>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
