import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import api from "../api/client";

function VerifyEmailPage() {
  const location = useLocation();
  const token = useMemo(() => new URLSearchParams(location.search).get("token") || "", [location.search]);
  const [status, setStatus] = useState(token ? "loading" : "error");
  const [message, setMessage] = useState(token ? "Verifying your email..." : "Missing verification token.");

  useEffect(() => {
    if (!token) return;

    const run = async () => {
      try {
        const { data } = await api.get(`/auth/verify-email?token=${encodeURIComponent(token)}`);
        setStatus("success");
        setMessage(data?.message || "Email verified successfully.");
      } catch (err) {
        setStatus("error");
        const detail = err?.response?.data?.detail;
        setMessage(typeof detail === "string" && detail.trim() ? detail : "Invalid or expired link");
      }
    };

    run();
  }, [token]);

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-2xl items-center justify-center px-4 py-8 sm:px-6 sm:py-10">
      <section className="card w-full p-6 sm:p-8">
        <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Email Verification</h1>

        {status === "loading" && <p className="mt-4 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700">{message}</p>}
        {status === "success" && <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p>}
        {status === "error" && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</p>}

        <div className="mt-6 text-center sm:text-left">
          <Link to="/login" className="btn-primary inline-flex">
            Go to Login
          </Link>
        </div>
      </section>
    </main>
  );
}

export default VerifyEmailPage;
