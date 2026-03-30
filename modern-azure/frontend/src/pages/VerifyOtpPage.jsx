import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import api from "../api/client";

function VerifyOtpPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state || {};

  const [email, setEmail] = useState(state.email || "");
  const [otp, setOtp] = useState("");
  const [message, setMessage] = useState(state.message || "Enter the OTP sent to your email.");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!state.email) {
      setMessage("Enter your email and OTP to verify your account.");
    }
  }, [state.email]);

  const onVerify = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!/^\d{6}$/.test(otp)) {
      setError("Please enter a valid 6-digit OTP.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/auth/verify-otp", {
        email,
        otp,
      });
      const successMessage = data?.message || "OTP verified successfully. Account created.";
      setSuccess(successMessage);
      setMessage("Verification completed. Redirecting to login...");
      setTimeout(() => {
        navigate("/login", {
          replace: true,
          state: { successMessage },
        });
      }, 1200);
    } catch (err) {
      setError(err?.response?.data?.detail || "Account verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const onResend = async () => {
    setError("");
    setSuccess("");
    setResending(true);
    try {
      const { data } = await api.post("/auth/resend-verification", { email });
      setMessage(data?.message || "A new OTP has been sent.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to resend OTP.");
    } finally {
      setResending(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-2xl items-center justify-center px-4 py-8 sm:px-6 sm:py-10">
      <section className="card w-full p-6 sm:p-8">
        <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Verify OTP</h1>
        <p className="mt-2 text-sm text-slate-600">Complete email verification to activate your account.</p>

        {message && <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p>}
        {success && <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">{success}</p>}
        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

        <form onSubmit={onVerify} className="mt-6 grid gap-4">
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
            <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="otp">
              OTP
            </label>
            <input
              id="otp"
              inputMode="numeric"
              placeholder="6-digit code"
              maxLength={6}
              required
              value={otp}
              onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
            />
          </div>

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Verifying..." : "Verify OTP"}
          </button>
          <button type="button" onClick={onResend} disabled={resending} className="btn-secondary">
            {resending ? "Resending..." : "Resend OTP"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600 sm:text-left">
          Back to <Link to="/register" className="font-semibold text-brand-700 hover:underline">registration</Link>
        </p>
      </section>
    </main>
  );
}

export default VerifyOtpPage;
