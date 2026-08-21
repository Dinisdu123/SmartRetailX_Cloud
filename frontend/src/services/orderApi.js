import axios from "axios";
import { API_BASE_URL } from "./config";

const orderApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

orderApi.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem("access_token");

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  return config;
});

export const getOrders = async () => {
  const response = await orderApi.get("/orders");
  return response.data;
};

export const getOrder = async (orderId) => {
  const response = await orderApi.get(`/orders/${orderId}`);
  return response.data;
};

export const createOrder = async (orderData) => {
  const response = await orderApi.post("/orders", orderData);
  return response.data;
};

export const updateOrderStatus = async (orderId, status) => {
  const response = await orderApi.put(`/orders/${orderId}/status`, {
    status,
  });

  return response.data;
};

export default orderApi;
