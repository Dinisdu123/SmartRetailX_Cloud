import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import Navbar from "../components/Navbar";

export default function Profile() {
  const { user, updateUser } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // --------------------------------------------------
  // Load user information into form
  // --------------------------------------------------

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setEmail(user.email || "");
    }
  }, [user]);

  // --------------------------------------------------
  // Update profile
  // --------------------------------------------------

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setSuccess("");
    setError("");

    try {
      const response = await api.put("/users/profile", {
        name: name.trim(),
        email: email.trim(),
      });

      console.log("Profile update response:", response.data);

      // Update global user state
      updateUser(response.data);

      setSuccess("Profile updated successfully.");
    } catch (error) {
      console.error("Profile update error:", error);

      if (error.response) {
        console.log("Status:", error.response.status);
        console.log("Response:", error.response.data);

        setError(error.response.data?.detail || "Failed to update profile.");
      } else if (error.request) {
        setError("Could not connect to the User Management Service.");
      } else {
        setError("Failed to update profile.");
      }
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // Loading state
  // --------------------------------------------------

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <p className="text-lg text-slate-600">Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Header */}

        <h1 className="text-4xl font-bold text-slate-900">My Profile</h1>

        <p className="text-xl text-slate-500 mt-3">
          Manage your account information.
        </p>

        {/* Profile card */}

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 mt-12 p-10">
          {/* Success message */}

          {success && (
            <div className="mb-8 rounded-xl border border-green-200 bg-green-50 px-6 py-5 text-green-700">
              {success}
            </div>
          )}

          {/* Error message */}

          {error && (
            <div className="mb-8 rounded-xl border border-red-200 bg-red-50 px-6 py-5 text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Name */}

            <div className="mb-8">
              <label className="block text-lg font-semibold text-slate-700 mb-3">
                Name
              </label>

              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-5 py-4 border border-slate-300 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-slate-800"
                required
                minLength={1}
                maxLength={100}
              />
            </div>

            {/* Email */}

            <div className="mb-10">
              <label className="block text-lg font-semibold text-slate-700 mb-3">
                Email
              </label>

              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-5 py-4 border border-slate-300 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-slate-800"
                required
              />
            </div>

            {/* Role and Status */}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
              <div className="bg-slate-50 rounded-xl p-6">
                <p className="text-lg text-slate-500">Role</p>

                <p className="text-2xl font-semibold text-slate-900 mt-2 capitalize">
                  {user.role}
                </p>
              </div>

              <div className="bg-slate-50 rounded-xl p-6">
                <p className="text-lg text-slate-500">Status</p>

                <p className="text-2xl font-semibold text-green-600 mt-2">
                  {user.is_active ? "Active" : "Inactive"}
                </p>
              </div>
            </div>

            {/* Save button */}

            <button
              type="submit"
              disabled={loading}
              className="bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white px-8 py-4 rounded-xl text-lg font-semibold transition"
            >
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
