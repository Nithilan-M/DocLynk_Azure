import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import api from "../api/client";
import PasswordInput from "../components/PasswordInput";

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

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const onSendOtp = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      const { data } = await api.post("/auth/forgot-password", { email });
      setOtpSent(true);
      setMessage(data?.message || "OTP sent. Check your email.");
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to send reset OTP."));
    } finally {
      setLoading(false);
    }
  };

  const onResetPassword = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!/^\d{6}$/.test(otp)) {
      setError("Please enter a valid 6-digit OTP.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/auth/reset-password-otp", {
        email,
        otp,
        new_password: newPassword,
      });
      const successMessage = data?.message || "Password reset successful.";
      setMessage(successMessage);
      setTimeout(() => {
        navigate("/login", {
          replace: true,
          state: { successMessage },
        });
      }, 1200);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to reset password."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-2xl items-center justify-center px-4 py-8 sm:px-6 sm:py-10">
      <section className="card w-full p-6 sm:p-8">
        <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Forgot Password</h1>
        <p className="mt-2 text-sm text-slate-600">Request OTP and reset your account password.</p>

        {message && <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p>}
        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

        {!otpSent ? (
          <form onSubmit={onSendOtp} className="mt-6 grid gap-4">
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

            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? "Sending OTP..." : "Send Reset OTP"}
            </button>
          </form>
        ) : (
          <form onSubmit={onResetPassword} className="mt-6 grid gap-4">
            <div>
              <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="otp">
                OTP
              </label>
              <input
                id="otp"
                inputMode="numeric"
                placeholder="6-digit OTP"
                maxLength={6}
                required
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="newPassword">
                New Password
              </label>
              <PasswordInput
                id="newPassword"
                minLength={8}
                required
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="confirmPassword">
                Confirm Password
              </label>
              <PasswordInput
                id="confirmPassword"
                minLength={8}
                required
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          </form>
        )}

        <p className="mt-5 text-center text-sm text-slate-600 sm:text-left">
          Back to{" "}
          <Link to="/login" className="font-semibold text-brand-700 hover:underline">
            login
          </Link>
        </p>
      </section>
    </main>
  );
}

export default ForgotPasswordPage;
