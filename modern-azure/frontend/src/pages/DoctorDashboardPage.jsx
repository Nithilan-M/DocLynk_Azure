import { useEffect, useState } from "react";

import api from "../api/client";
import TopBar from "../components/TopBar";

function DoctorDashboardPage() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAppointments = async () => {
    setLoading(true);
    setError("");

    try {
      const { data } = await api.get("/appointments");
      setAppointments(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load appointments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  const updateStatus = async (appointmentId, status) => {
    setError("");
    try {
      await api.put(`/appointments/${appointmentId}/status`, { status });
      await loadAppointments();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to update appointment status.");
    }
  };

  return (
    <>
      <TopBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Doctor Dashboard</h1>
        <p className="mt-2 text-sm text-slate-600">Review and manage incoming appointment requests.</p>

        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

        <section className="card mt-6 p-4 sm:p-5">
          <h2 className="font-heading text-xl font-semibold text-slate-900">Appointment queue</h2>
          {loading ? (
            <p className="mt-4 text-sm text-slate-500">Loading appointments...</p>
          ) : appointments.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">No appointments assigned yet.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {appointments.map((appointment) => (
                <li key={appointment.id} className="rounded-xl border border-slate-200 bg-white p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-900">
                        {appointment.patient_name || `Patient #${appointment.patient_id}`}
                      </p>
                      <p className="text-sm text-slate-500">{new Date(appointment.scheduled_at).toLocaleString()}</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                      {appointment.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{appointment.reason || "No reason provided."}</p>

                  {appointment.status === "pending" && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => updateStatus(appointment.id, "approved")}
                        className="flex-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-emerald-700 sm:flex-none"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        onClick={() => updateStatus(appointment.id, "rejected")}
                        className="flex-1 rounded-lg bg-rose-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-rose-700 sm:flex-none"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </>
  );
}

export default DoctorDashboardPage;
