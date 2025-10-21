"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import Image from "next/image";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://sms-8kiu.onrender.com" || "http://localhost:8000";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // OAuth2 password flow expects application/x-www-form-urlencoded body
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const response = await axios.post(`${API_BASE_URL}/token`, params, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      const { access_token } = response.data;
      localStorage.setItem("token", access_token);
      router.push("/");
    } catch (err) {
      // Surface detailed error for debugging (validation / CORS / network)
      console.error("Login error", err);
      const detail =
        err.response?.data?.detail ?? err.response?.data ?? err.message;
      setError(
        typeof detail === "object"
          ? JSON.stringify(detail)
          : detail || "Login failed"
      );
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-light d-flex align-items-center justify-content-center">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-md-6 col-lg-4">
            <div className="card shadow">
              <div className="card-body p-5">
                <div className="text-center mb-4">
                  <Image
                    src="/Big Bang logo-icn.png"
                    alt="SMS Sender logo"
                    className="img-fluid mb-3"
                    width={160}
                    height={100}
                    style={{ maxHeight: "60px", width: "auto", height: "auto" }}
                  />
                  <h3 className="card-title">Login</h3>
                </div>

                <form onSubmit={handleSubmit}>
                  <div className="mb-3">
                    <label htmlFor="email" className="form-label">
                      Email
                    </label>
                    <input
                      type="email"
                      className="form-control"
                      id="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="password" className="form-label">
                      Password
                    </label>
                    <input
                      type="password"
                      className="form-control"
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>

                  {error && (
                    <div className="alert alert-danger" role="alert">
                      {error}
                    </div>
                  )}

                  <div className="d-grid">
                    <button
                      type="submit"
                      className="btn btn-primary btn-lg"
                      disabled={loading}
                    >
                      {loading ? "Logging in..." : "Login"}
                    </button>
                  </div>
                </form>

                <div className="text-center mt-3">
                  <p className="mb-0">
                    Don&apos;t have an account?{" "}
                    <a href="/register" className="text-decoration-none">
                      Register here
                    </a>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
