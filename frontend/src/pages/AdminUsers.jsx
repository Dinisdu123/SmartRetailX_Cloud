import { useEffect, useState } from "react";
import api from "../services/api";
import Navbar from "../components/Navbar";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // --------------------------------------------------
  // Load users
  // --------------------------------------------------

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/users");

      setUsers(response.data);
    } catch (error) {
      console.error("Failed to load users:", error);

      if (error.response?.status === 403) {
        setError("You do not have permission to access this page.");
      } else if (error.response?.status === 401) {
        setError("Your session has expired. Please login again.");
      } else {
        setError("Failed to load users.");
      }
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // Load users when page opens
  // --------------------------------------------------

  useEffect(() => {
    loadUsers();
  }, []);

  // --------------------------------------------------
  // Delete/deactivate user
  // --------------------------------------------------

  const handleDelete = async (userId, userName) => {
    const confirmed = window.confirm(
      `Are you sure you want to deactivate ${userName}?`
    );

    if (!confirmed) {
      return;
    }

    try {
      await api.delete(`/users/${userId}`);

      // Remove user from current UI
      setUsers((currentUsers) =>
        currentUsers.filter((user) => user.id !== userId)
      );
    } catch (error) {
      console.error("Failed to deactivate user:", error);

      alert(error.response?.data?.detail || "Failed to deactivate user.");
    }
  };

  // --------------------------------------------------
  // Loading
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100">
        <Navbar />

        <main className="max-w-7xl mx-auto px-6 py-10">
          <p className="text-lg text-slate-600">Loading users...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}

        <div className="mb-10">
          <h1 className="text-4xl font-bold text-slate-900">User Management</h1>

          <p className="text-xl text-slate-500 mt-3">
            Manage SmartRetailX users and accounts.
          </p>
        </div>

        {/* Error */}

        {error && (
          <div className="mb-8 rounded-xl border border-red-200 bg-red-50 px-6 py-5 text-red-700">
            {error}
          </div>
        )}

        {/* Statistics */}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <p className="text-slate-500 text-lg">Total Users</p>

            <p className="text-4xl font-bold text-slate-900 mt-2">
              {users.length}
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <p className="text-slate-500 text-lg">Administrators</p>

            <p className="text-4xl font-bold text-slate-900 mt-2">
              {users.filter((user) => user.role === "admin").length}
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <p className="text-slate-500 text-lg">Customers</p>

            <p className="text-4xl font-bold text-slate-900 mt-2">
              {users.filter((user) => user.role === "customer").length}
            </p>
          </div>
        </div>

        {/* Users table */}

        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          <div className="px-8 py-6 border-b border-slate-200">
            <h2 className="text-2xl font-bold text-slate-900">All Users</h2>
          </div>

          {users.length === 0 ? (
            <div className="p-10 text-center text-slate-500">
              No active users found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-8 py-5 text-sm font-semibold text-slate-600">
                      User
                    </th>

                    <th className="text-left px-8 py-5 text-sm font-semibold text-slate-600">
                      Email
                    </th>

                    <th className="text-left px-8 py-5 text-sm font-semibold text-slate-600">
                      Role
                    </th>

                    <th className="text-left px-8 py-5 text-sm font-semibold text-slate-600">
                      Status
                    </th>

                    <th className="text-right px-8 py-5 text-sm font-semibold text-slate-600">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {users.map((user) => (
                    <tr
                      key={user.id}
                      className="border-t border-slate-200 hover:bg-slate-50"
                    >
                      {/* User */}

                      <td className="px-8 py-6">
                        <div className="font-semibold text-slate-900 text-lg">
                          {user.name}
                        </div>

                        <div className="text-sm text-slate-400 mt-1">
                          {user.id}
                        </div>
                      </td>

                      {/* Email */}

                      <td className="px-8 py-6 text-slate-600">{user.email}</td>

                      {/* Role */}

                      <td className="px-8 py-6">
                        <span
                          className={
                            user.role === "admin"
                              ? "inline-flex px-3 py-1 rounded-full text-sm font-semibold bg-purple-100 text-purple-700"
                              : "inline-flex px-3 py-1 rounded-full text-sm font-semibold bg-blue-100 text-blue-700"
                          }
                        >
                          {user.role}
                        </span>
                      </td>

                      {/* Status */}

                      <td className="px-8 py-6">
                        <span className="inline-flex px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-700">
                          Active
                        </span>
                      </td>

                      {/* Action */}

                      <td className="px-8 py-6 text-right">
                        {user.role === "admin" ? (
                          <span className="text-sm text-slate-400">
                            Protected
                          </span>
                        ) : (
                          <button
                            onClick={() => handleDelete(user.id, user.name)}
                            className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold"
                          >
                            Deactivate
                          </button>
                        )}
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
