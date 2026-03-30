import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-white/70 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link to={user?.is_admin ? "/admin" : user?.role === "doctor" ? "/doctor" : "/patient"} className="font-heading text-xl font-bold text-brand-700">
          DocLynk
        </Link>
        <div className="flex min-w-0 items-center gap-2 sm:gap-4">
          <p className="hidden max-w-[10rem] truncate text-sm font-medium text-slate-600 sm:block">{user?.full_name}</p>
          <button type="button" onClick={handleLogout} className="btn-secondary px-3 py-1.5 text-xs sm:text-sm">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
