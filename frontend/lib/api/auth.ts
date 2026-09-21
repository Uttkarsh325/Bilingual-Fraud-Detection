import { apiClient } from "./client";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  username: string;
  expires_in?: number;
}

export interface UserInfo {
  user_id: number;
  username: string;
  created_at: string;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", { username, password });
  return data;
}

export async function registerUser(username: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", { username, password });
  return data;
}

export async function fetchMe(): Promise<UserInfo> {
  const { data } = await apiClient.get<UserInfo>("/auth/me");
  return data;
}