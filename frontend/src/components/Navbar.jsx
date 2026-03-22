import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <nav className="bg-white border-b px-6 py-4 flex items-center justify-between">
      <Link to="/" className="text-xl font-bold text-blue-500">Marketplace</Link>
      <div className="flex gap-4 items-center">
        <Link to="/products">Products</Link>
        <Link to="/cart">Cart</Link>
        {user ? (
          <>
            <Link to="/orders">Orders</Link>
            <Link to="/profile">Profile</Link>
            <button className="text-red-500" onClick={async()=>{await logout();navigate('/');}}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register" className="text-blue-500">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}
