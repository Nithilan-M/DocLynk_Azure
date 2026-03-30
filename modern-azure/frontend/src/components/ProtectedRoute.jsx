import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function redirectPathForUser(user) {
  if (user?.is_admin) {
    return "/admin";
  }
  return user?.role === "doctor" ? "/doctor" : "/patient";
}

function ProtectedRoute({ children, allowedRoles, requireAdmin = false }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={redirectPathForUser(user)} replace />;
  }

  if (requireAdmin && !user?.is_admin) {
    return <Navigate to={redirectPathForUser(user)} replace />;
  }

  return children;
}

export default ProtectedRoute;
