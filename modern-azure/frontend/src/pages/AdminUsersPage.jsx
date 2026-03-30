import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client";
import TopBar from "../components/TopBar";

function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    if (role) params.set("role", role);
    return params.toString();
  }, [search, role]);

  const loadUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/admin/users${queryString ? `?${queryString}` : ""}`);
      setUsers(data.users || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load users.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [queryString]);

  const editUser = async (user) => {
    const name = window.prompt("Name", user.name);
    if (name === null) return;
    const email = window.prompt("Email", user.email);
    if (email === null) return;
    const roleValue = window.prompt("Role (doctor/patient)", user.role);
    if (roleValue === null) return;

    try {
      await api.put(`/admin/users/${user.id}`, {
        name,
        email,
        role: roleValue,
      });
      await loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update user.");
    }
  };

  const toggleAdmin = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/toggle-admin`);
      await loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update admin status.");
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm("Delete this user and related appointments?")) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      await loadUsers();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete user.");
    }
  };

  return (
    <>
      <TopBar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="font-heading text-2xl font-bold text-slate-900 sm:text-3xl">Admin Users</h1>
          <Link to="/admin" className="btn-secondary w-full text-center text-sm sm:w-auto">
            Back to Dashboard
          </Link>
        </div>

        {error && <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

        <section className="card mt-6 p-4">
          <div className="grid gap-3 md:grid-cols-[1fr,180px,120px]">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name/email"
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2"
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2"
            >
              <option value="">All roles</option>
              <option value="doctor">Doctor</option>
              <option value="patient">Patient</option>
            </select>
            <button type="button" className="btn-primary w-full md:w-auto" onClick={loadUsers}>
              Apply
            </button>
          </div>
        </section>

        <section className="card mt-4 overflow-hidden">
          {loading ? (
            <p className="p-4 text-sm text-slate-500">Loading users...</p>
          ) : users.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">No users found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-[760px] text-sm md:min-w-full">
                <thead className="bg-slate-50 text-left text-slate-600">
                  <tr>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">Email</th>
                    <th className="px-4 py-3">Role</th>
                    <th className="px-4 py-3">Admin</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-t border-slate-200">
                      <td className="px-4 py-3">{user.name}</td>
                      <td className="px-4 py-3">{user.email}</td>
                      <td className="px-4 py-3">{user.role}</td>
                      <td className="px-4 py-3">{user.is_admin ? "Yes" : "No"}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button type="button" className="btn-secondary text-xs" onClick={() => editUser(user)}>
                            Edit
                          </button>
                          <button type="button" className="btn-secondary text-xs" onClick={() => toggleAdmin(user.id)}>
                            {user.is_admin ? "Revoke Admin" : "Make Admin"}
                          </button>
                          <button
                            type="button"
                            className="rounded-lg border border-rose-300 px-2 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50"
                            onClick={() => deleteUser(user.id)}
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

export default AdminUsersPage;
