import axios from "axios";
import { API_BASE_URL } from "./config";

const productApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

productApi.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("access_token");

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export const getProducts = async (filters = {}) => {
  const response = await productApi.get("/products", { params: filters });
  return response.data;
};

export const getProduct = async (productId) => {
  const response = await productApi.get(`/products/${productId}`);
  return response.data;
};

export const createProduct = async (productData) => {
  const response = await productApi.post("/products", productData);
  return response.data;
};

export const updateProduct = async (productId, productData) => {
  const response = await productApi.put(`/products/${productId}`, productData);
  return response.data;
};

export const deleteProduct = async (productId) => {
  const response = await productApi.delete(`/products/${productId}`);
  return response.data;
};

export default productApi;
