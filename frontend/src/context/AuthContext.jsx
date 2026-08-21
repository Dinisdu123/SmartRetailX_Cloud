import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ============================================================
  // LOAD CURRENT USER
  // ============================================================

  const loadUser = async () => {
    const accessToken = localStorage.getItem("access_token");

    if (!accessToken) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get("/users/profile");

      setUser(response.data);
    } catch (error) {
      console.error(
        "Failed to load user:",
        error.response?.data || error.message
      );

      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  // ============================================================
  // LOGIN
  // ============================================================

  const login = async (email, password) => {
    try {
      const response = await api.post("/users/login", {
        email: email.trim(),
        password,
      });

      console.log("LOGIN RESPONSE:", response.data);

      const { access_token, refresh_token } = response.data;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);

      // Get logged-in user's profile
      const profileResponse = await api.get("/users/profile");

      console.log("PROFILE RESPONSE:", profileResponse.data);

      setUser(profileResponse.data);

      return profileResponse.data;
    } catch (error) {
      console.error("LOGIN ERROR:", error.response?.data || error.message);

      throw error;
    }
  };

  // ============================================================
  // REGISTER
  // ============================================================

  const register = async (name, email, password) => {
    try {
      const response = await api.post("/users/register", {
        name: name.trim(),
        email: email.trim(),
        password,
      });

      console.log("REGISTER RESPONSE:", response.data);

      return response.data;
    } catch (error) {
      console.error("REGISTER ERROR:", error.response?.data || error.message);

      throw error;
    }
  };

  // ============================================================
  // UPDATE USER
  // ============================================================

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
  };

  // ============================================================
  // LOGOUT
  // ============================================================

  const logout = async () => {
    try {
      await api.post("/users/logout");
    } catch (error) {
      console.error("Logout API error:", error.response?.data || error.message);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        updateUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
