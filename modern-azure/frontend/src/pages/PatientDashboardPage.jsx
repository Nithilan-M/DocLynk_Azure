import { useCallback, useEffect, useMemo, useState } from "react";

import api from "../api/client";
import TopBar from "../components/TopBar";

function PatientDashboardPage() {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [error, setError] = useState("");
  const [bookForm, setBookForm] = useState({
    doctor_id: "",
    date: "",
    time_slot: "",
    reason: "",
  });

  const doctorsById = useMemo(() => {
    const map = new Map();
    doctors.forEach((doctor) => map.set(doctor.id, doctor));
    return map;
  }, [doctors]);

  const loadData = async () => {
    setLoading(true);
    setError("");

    try {
      const [doctorRes, appointmentRes] = await Promise.all([api.get("/users/doctors"), api.get("/appointments")]);
      setDoctors(doctorRes.data);
      setAppointments(appointmentRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const fetchSlots = useCallback(async () => {
    if (!bookForm.doctor_id || !bookForm.date) {
      setAvailableSlots([]);
      setBookForm((prev) => ({ ...prev, time_slot: "" }));
      return;
    }

    setLoadingSlots(true);
    try {
      const params = {
        doctor_id: Number(bookForm.doctor_id),
        date: bookForm.date,
      };

      let data;
      try {
        const response = await api.get("/appointments/available-slots", { params });
        data = response.data;
      } catch (primaryErr) {
        const statusCode = primaryErr?.response?.status;
        if (statusCode !== 404 && statusCode !== 405) {
          throw primaryErr;
        }
        const fallbackResponse = await api.get("/appointments/availability", { params });
        data = fallbackResponse.data;
      }

      setAvailableSlots(data.available_slots || []);
      setError("");
      setBookForm((prev) => ({ ...prev, time_slot: "" }));
    } catch (err) {
      setAvailableSlots([]);
      setError(err.response?.data?.detail || "Failed to load available slots.");
    } finally {
      setLoadingSlots(false);
    }
  }, [bookForm.doctor_id, bookForm.date]);

  useEffect(() => {
    fetchSlots();
  }, [fetchSlots]);

  const handleBook = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await api.post("/appointments", {
        doctor_id: Number(bookForm.doctor_id),
        date: bookForm.date,
        time_slot: bookForm.time_slot,
        reason: bookForm.reason || null,
      });
      setBookForm({ doctor_id: "", date: "", time_slot: "", reason: "" });
      setAvailableSlots([]);
      await loadData();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail === "Slot already booked") {
        alert("This slot was just booked, please choose another");
        setBookForm((prev) => ({ ...prev, time_slot: "" }));
        await fetchSlots();
      }
      setError(detail || "Unable to book appointment.");
    } finally {
      setSubmitting(false);
    }
  };

  const cancelAppointment = async (appointmentId) => {
    setError("");
    try {
      await api.delete(`/appointments/${appointmentId}`);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to cancel appointment.");
    }
  };

  return (
    <>
      <TopBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Patient Dashboard</h1>
        <p className="mt-2 text-sm text-slate-600">Manage upcoming care in one place.</p>

        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr,1.4fr]">
          <form onSubmit={handleBook} className="card p-4 sm:p-5">
            <h2 className="font-heading text-xl font-semibold text-slate-900">Book appointment</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="doctorId">
                  Doctor
                </label>
                <select
                  id="doctorId"
                  value={bookForm.doctor_id}
                  onChange={(event) =>
                    setBookForm((prev) => ({
                      ...prev,
                      doctor_id: event.target.value,
                      time_slot: "",
                    }))
                  }
                  required
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
                >
                  <option value="">Select a doctor</option>
                  {doctors.map((doctor) => (
                    <option key={doctor.id} value={doctor.id}>
                      {doctor.full_name}{doctor.specialization ? ` (${doctor.specialization})` : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="appointmentDate">
                  Date
                </label>
                <input
                  id="appointmentDate"
                  type="date"
                  value={bookForm.date}
                  onChange={(event) =>
                    setBookForm((prev) => ({
                      ...prev,
                      date: event.target.value,
                      time_slot: "",
                    }))
                  }
                  required
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="timeSlot">
                  Available time slot
                </label>
                <select
                  id="timeSlot"
                  value={bookForm.time_slot}
                  onChange={(event) => setBookForm((prev) => ({ ...prev, time_slot: event.target.value }))}
                  required
                  disabled={!bookForm.doctor_id || !bookForm.date || loadingSlots || availableSlots.length === 0}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2 disabled:bg-slate-100"
                >
                  <option value="">{loadingSlots ? "Loading slots..." : "Select a time slot"}</option>
                  {availableSlots.map((slot) => (
                    <option key={slot} value={slot}>
                      {slot}
                    </option>
                  ))}
                </select>
                {!loadingSlots && bookForm.doctor_id && bookForm.date && availableSlots.length === 0 && (
                  <p className="mt-1 text-xs text-rose-600">No slots available for this date.</p>
                )}
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold text-slate-700" htmlFor="reason">
                  Reason (optional)
                </label>
                <textarea
                  id="reason"
                  rows={3}
                  value={bookForm.reason}
                  onChange={(event) => setBookForm((prev) => ({ ...prev, reason: event.target.value }))}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none ring-brand-500 transition focus:ring-2"
                />
              </div>

              <button type="submit" disabled={submitting} className="btn-primary w-full">
                {submitting ? "Booking..." : "Book Appointment"}
              </button>
            </div>
          </form>

          <section className="card p-4 sm:p-5">
            <h2 className="font-heading text-xl font-semibold text-slate-900">Your appointments</h2>
            {loading ? (
              <p className="mt-4 text-sm text-slate-500">Loading appointments...</p>
            ) : appointments.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">No appointments yet.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {appointments.map((appointment) => {
                  const doctor = doctorsById.get(appointment.doctor_id);
                  return (
                    <li key={appointment.id} className="rounded-xl border border-slate-200 bg-white p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="font-semibold text-slate-900">
                            {appointment.doctor_name || doctor?.full_name || `Doctor #${appointment.doctor_id}`}
                          </p>
                          <p className="text-sm text-slate-500">
                            {new Date(appointment.scheduled_at).toLocaleString([], {
                              hour12: false,
                            })}
                          </p>
                        </div>
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
                          {appointment.status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{appointment.reason || "No reason provided."}</p>
                      {(appointment.status === "pending" || appointment.status === "approved") && (
                        <button
                          type="button"
                          onClick={() => cancelAppointment(appointment.id)}
                          className="mt-3 rounded-lg border border-rose-300 px-3 py-1.5 text-sm font-semibold text-rose-700 transition hover:bg-rose-50"
                        >
                          Cancel
                        </button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </section>
      </main>
    </>
  );
}

export default PatientDashboardPage;
