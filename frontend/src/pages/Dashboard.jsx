import Navbar from "../components/Navbar";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">
            Welcome, {user?.name}
          </h1>

          <p className="text-slate-500 mt-2">
            Welcome to your SmartRetailX dashboard.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
            <p className="text-sm text-slate-500">Account Status</p>

            <p className="text-2xl font-bold text-green-600 mt-2">Active</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
            <p className="text-sm text-slate-500">Account Role</p>

            <p className="text-2xl font-bold text-slate-900 mt-2 capitalize">
              {user?.role}
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
            <p className="text-sm text-slate-500">Member Since</p>

            <p className="text-lg font-bold text-slate-900 mt-2">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString()
                : "-"}
            </p>
          </div>
        </div>

        <div className="mt-8 bg-white rounded-xl p-8 shadow-sm border border-slate-200">
          <h2 className="text-xl font-bold text-slate-900">
            SmartRetailX Platform
          </h2>

          <p className="text-slate-500 mt-2">
            Your account is connected to the SmartRetailX distributed commerce
            platform.
          </p>
        </div>
      </main>
    </div>
  );
}
