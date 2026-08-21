import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isAdmin = user?.role === "admin";

  return (
    <nav className="bg-slate-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <Link to="/dashboard" className="text-xl font-bold tracking-tight">
            SmartRetailX
          </Link>

          <div className="flex flex-wrap items-center gap-5">
            <Link
              to="/dashboard"
              className="text-slate-300 hover:text-white transition"
            >
              Dashboard
            </Link>

            <Link
              to={isAdmin ? "/admin/products" : "/products"}
              className="text-slate-300 hover:text-white transition"
            >
              Products
            </Link>

            <Link
              to="/orders"
              className="text-slate-300 hover:text-white transition"
            >
              Orders
            </Link>

            <Link
              to="/profile"
              className="text-slate-300 hover:text-white transition"
            >
              Profile
            </Link>

            {isAdmin && (
              <>
                <Link
                  to="/admin/users"
                  className="text-slate-300 hover:text-white transition"
                >
                  Users
                </Link>

                <Link
                  to="/admin/inventory"
                  className="text-slate-300 hover:text-white transition"
                >
                  Inventory
                </Link>
              </>
            )}

            <div className="border-l border-slate-700 pl-5 flex items-center gap-4">
              <span className="text-sm text-slate-300">{user?.name}</span>

              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg text-sm font-medium transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
