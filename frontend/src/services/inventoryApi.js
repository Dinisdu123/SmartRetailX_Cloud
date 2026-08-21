import axios from "axios";
import { API_BASE_URL } from "./config";

const inventoryApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

inventoryApi.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem("access_token");

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

export const getInventory = async () => {
  const response = await inventoryApi.get("/inventory");
  return response.data;
};

export default inventoryApi;
