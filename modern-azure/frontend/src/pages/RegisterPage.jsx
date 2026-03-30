import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import api from "../api/client";
import PasswordInput from "../components/PasswordInput";

function getApiErrorMessage(err, fallback) {
  if (err?.code === "ERR_NETWORK") {
    return "Cannot reach backend API. Ensure FastAPI is running and VITE_API_URL is correct.";
  }
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

function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "patient",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    const payload = {
      full_name: form.full_name,
      email: form.email,
      password: form.password,
      role: form.role,
      specialization: null,
    };

    try {
      const { data } = await api.post("/auth/register", payload);
      navigate("/verify-otp", {
        state: {
          email: data.email,
          message: data.message,
        },
      });
    } catch (err) {
      setError(getApiErrorMessage(err, "Registration failed. Please check your details."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-3xl items-center justify-center px-4 py-8 sm:px-6 sm:py-10">
      <section className="card w-full animate-rise p-6 sm:p-8">
        <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Create your account</h1>
        <p className="mt-2 text-sm text-slate-600">Register as a patient or a doctor.</p>

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="fullName">
              Full name
            </label>
            <input
              id="fullName"
              required
              value={form.full_name}
              onChange={(event) => updateField("full_name", event.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="password">
              Password
            </label>
            <PasswordInput
              id="password"
              minLength={8}
              required
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="role">
              Role
            </label>
            <select
              id="role"
              value={form.role}
              onChange={(event) => updateField("role", event.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
            </select>
          </div>

          {error && <p className="sm:col-span-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

          <button type="submit" disabled={loading} className="btn-primary sm:col-span-2">
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600 sm:text-left">
          Already registered?{" "}
          <Link to="/login" className="font-semibold text-brand-700 hover:underline">
            Login
          </Link>
        </p>
      </section>
    </main>
  );
}

export default RegisterPage;
