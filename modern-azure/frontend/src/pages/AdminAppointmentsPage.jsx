import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client";
import TopBar from "../components/TopBar";

function AdminAppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [doctorFilter, setDoctorFilter] = useState("");
  const [seedMessage, setSeedMessage] = useState("");

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (doctorFilter) params.set("doctor_id", doctorFilter);
    return params.toString();
  }, [statusFilter, doctorFilter]);

  const loadAppointments = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/admin/appointments${queryString ? `?${queryString}` : ""}`);
      setAppointments(data.appointments || []);
      setDoctors(data.doctors || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load appointments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, [queryString]);

  const updateStatus = async (appointmentId, status) => {
    try {
      await api.put(`/admin/appointments/${appointmentId}/status`, { status });
      await loadAppointments();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update status.");
    }
  };

  const deleteAppointment = async (appointmentId) => {
    if (!window.confirm("Delete this appointment?")) return;
    try {
      await api.delete(`/admin/appointments/${appointmentId}`);
      await loadAppointments();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete appointment.");
    }
  };

  const seedMissingAppointments = async () => {
    const seedDate = window.prompt("Seed date (YYYY-MM-DD). Leave blank for tomorrow:", "");
    if (seedDate === null) return;

    setError("");
    setSeedMessage("");

    try {
      const payload = seedDate.trim() ? { date: seedDate.trim() } : {};
      const { data } = await api.post("/admin/appointments/seed-missing", payload);
      setSeedMessage(`Created ${data.created} appointments, skipped ${data.skipped} doctors for ${data.target_date}.`);
      await loadAppointments();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to seed missing doctor appointments.");
    }
  };

  return (
    <>
      <TopBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Admin Appointments</h1>
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
            <button type="button" className="btn-secondary w-full text-sm sm:w-auto" onClick={seedMissingAppointments}>
              Seed Missing Doctor Appointments
            </button>
            <Link to="/admin" className="btn-secondary w-full text-center text-sm sm:w-auto">
              Back to Dashboard
            </Link>
          </div>
        </div>

        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        {seedMessage && <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{seedMessage}</p>}

        <section className="card mt-6 p-4">
          <div className="grid gap-3 md:grid-cols-[180px,1fr,120px]">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="completed">Completed</option>
            </select>
            <select
              value={doctorFilter}
              onChange={(e) => setDoctorFilter(e.target.value)}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2"
            >
              <option value="">All Doctors</option>
              {doctors.map((doctor) => (
                <option key={doctor.id} value={doctor.id}>
                  Dr. {doctor.name}
                </option>
              ))}
            </select>
            <button type="button" className="btn-primary w-full md:w-auto" onClick={loadAppointments}>
              Apply
            </button>
          </div>
        </section>

        <section className="card mt-4 overflow-hidden">
          {loading ? (
            <p className="p-4 text-sm text-slate-500">Loading appointments...</p>
          ) : appointments.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">No appointments found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-[860px] text-sm md:min-w-full">
                <thead className="bg-slate-50 text-left text-slate-600">
                  <tr>
                    <th className="px-4 py-3">Patient</th>
                    <th className="px-4 py-3">Doctor</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Time</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.map((appointment) => (
                    <tr key={appointment.id} className="border-t border-slate-200">
                      <td className="px-4 py-3">{appointment.patient_name}</td>
                      <td className="px-4 py-3">{appointment.doctor_name}</td>
                      <td className="px-4 py-3">{appointment.date}</td>
                      <td className="px-4 py-3">{appointment.time_slot}</td>
                      <td className="px-4 py-3">{appointment.status}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button type="button" className="btn-secondary text-xs" onClick={() => updateStatus(appointment.id, "approved")}>
                            Approve
                          </button>
                          <button type="button" className="btn-secondary text-xs" onClick={() => updateStatus(appointment.id, "rejected")}>
                            Reject
                          </button>
                          <button type="button" className="btn-secondary text-xs" onClick={() => updateStatus(appointment.id, "completed")}>
                            Complete
                          </button>
                          <button
                            type="button"
                            className="rounded-lg border border-rose-300 px-2 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50"
                            onClick={() => deleteAppointment(appointment.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </>
  );
}

export default AdminAppointmentsPage;
