import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client";
import TopBar from "../components/TopBar";

function AdminDashboardPage() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [seedMessage, setSeedMessage] = useState("");
  const [seeding, setSeeding] = useState(false);

  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/admin/dashboard");
      setPayload(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load admin dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const seedMissingAppointments = async () => {
    const seedDate = window.prompt("Seed date (YYYY-MM-DD). Leave blank for tomorrow:", "");
    if (seedDate === null) return;

    setError("");
    setSeedMessage("");
    setSeeding(true);
    try {
      const payloadBody = seedDate.trim() ? { date: seedDate.trim() } : {};
      const { data } = await api.post("/admin/appointments/seed-missing", payloadBody);
      setSeedMessage(`Created ${data.created} appointments, skipped ${data.skipped} doctors for ${data.target_date}.`);
      await loadDashboard();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to seed missing doctor appointments.");
    } finally {
      setSeeding(false);
    }
  };

  const stats = payload?.stats;

  return (
    <>
      <TopBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Admin Dashboard</h1>
            <p className="mt-2 text-sm text-slate-600">Manage users and appointments across the platform.</p>
          </div>
          <button type="button" className="btn-secondary w-full text-sm sm:w-auto" onClick={seedMissingAppointments} disabled={seeding}>
            {seeding ? "Seeding..." : "Seed Missing Doctor Appointments"}
          </button>
        </div>

        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        {seedMessage && <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{seedMessage}</p>}

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Loading dashboard...</p>
        ) : (
          <>
            <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Total Users</p>
                <p className="mt-2 font-heading text-3xl font-bold text-slate-900">{stats?.total_users ?? 0}</p>
              </div>
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Doctors</p>
                <p className="mt-2 font-heading text-3xl font-bold text-slate-900">{stats?.total_doctors ?? 0}</p>
              </div>
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Patients</p>
                <p className="mt-2 font-heading text-3xl font-bold text-slate-900">{stats?.total_patients ?? 0}</p>
              </div>
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Appointments</p>
                <p className="mt-2 font-heading text-3xl font-bold text-slate-900">{stats?.total_appointments ?? 0}</p>
              </div>
            </section>

            <section className="mt-4 grid gap-4 sm:grid-cols-3">
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Pending</p>
                <p className="mt-1 text-2xl font-semibold text-amber-600">{stats?.pending_appointments ?? 0}</p>
              </div>
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Approved</p>
                <p className="mt-1 text-2xl font-semibold text-emerald-600">{stats?.approved_appointments ?? 0}</p>
              </div>
              <div className="card p-4 sm:p-5">
                <p className="text-xs uppercase tracking-wide text-slate-500">Rejected</p>
                <p className="mt-1 text-2xl font-semibold text-rose-600">{stats?.rejected_appointments ?? 0}</p>
              </div>
            </section>

            <section className="mt-6 grid gap-4 sm:grid-cols-2">
              <Link to="/admin/users" className="card p-4 transition hover:shadow-lg sm:p-5">
                <h2 className="font-heading text-xl font-semibold text-slate-900">Manage Users</h2>
                <p className="mt-1 text-sm text-slate-600">Search, edit, promote admins, and remove users.</p>
              </Link>
              <Link to="/admin/appointments" className="card p-4 transition hover:shadow-lg sm:p-5">
                <h2 className="font-heading text-xl font-semibold text-slate-900">Manage Appointments</h2>
                <p className="mt-1 text-sm text-slate-600">Filter, approve/reject, complete, and delete appointments.</p>
              </Link>
            </section>

            <section className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="card p-4 sm:p-5">
                <h3 className="font-heading text-xl font-semibold text-slate-900">Recent Users</h3>
                <ul className="mt-3 space-y-2">
                  {(payload?.recent_users || []).map((user) => (
                    <li key={user.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
                      <p className="font-semibold text-slate-900">{user.name}</p>
                      <p className="text-slate-500">{user.email}</p>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="card p-4 sm:p-5">
                <h3 className="font-heading text-xl font-semibold text-slate-900">Recent Appointments</h3>
                <ul className="mt-3 space-y-2">
                  {(payload?.recent_appointments || []).map((appointment) => (
                    <li key={appointment.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
                      <p className="font-semibold text-slate-900">{appointment.patient_name}</p>
                      <p className="text-slate-500">
                        Dr. {appointment.doctor_name} • {appointment.date} {appointment.time_slot}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          </>
        )}
      </main>
    </>
  );
}

export default AdminDashboardPage;
