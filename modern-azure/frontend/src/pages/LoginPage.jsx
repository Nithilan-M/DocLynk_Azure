import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import api from "../api/client";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";

function getApiErrorMessage(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "string") {
      return first;
    }
    if (first && typeof first.msg === "string") {
      return first.msg;
    }
  }
  return fallback;
}

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const successMessage = location.state?.successMessage || "";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { data } = await api.post("/auth/login", { email, password });
      login(data.access_token, data.user);
      if (data.user.is_admin) {
        navigate("/admin");
      } else {
        navigate(data.user.role === "doctor" ? "/doctor" : "/patient");
      }
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to login. Please verify your credentials."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-xl items-center justify-center px-4 sm:px-6">
      <section className="card w-full animate-rise p-8 sm:p-10">
        <header className="text-center">
          <h1 className="font-heading text-3xl font-bold text-slate-900">DocLynk</h1>
          <h2 className="mt-2 font-heading text-2xl font-bold text-slate-900">Sign in</h2>
          <p className="mt-2 text-sm text-slate-600">Use your account credentials to continue.</p>
        </header>

        {successMessage && <p className="mt-5 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{successMessage}</p>}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4 text-left">
          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="password">
              Password
            </label>
            <PasswordInput
              id="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <div className="text-right">
            <Link to="/forgot-password" className="text-sm font-semibold text-brand-700 hover:underline">
              Forgot password?
            </Link>
          </div>

          {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          Need an account?{" "}
          <Link to="/register" className="font-semibold text-brand-700 hover:underline">
            Register
          </Link>
        </p>
      </section>
    </main>
  );
}

export default LoginPage;
