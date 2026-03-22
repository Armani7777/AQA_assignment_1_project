import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();
  const submit = async (e) => { e.preventDefault(); try { await login(email, password); navigate("/"); } catch { setError("Invalid credentials"); } };
  return <form onSubmit={submit} className="max-w-md mx-auto bg-white p-6 rounded"><h1 className="text-xl font-semibold mb-4">Login</h1>{error && <p className="text-red-500 mb-2">{error}</p>}<input className="border rounded p-2 w-full mb-2" placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} /><input className="border rounded p-2 w-full mb-2" type="password" placeholder="Password" value={password} onChange={(e)=>setPassword(e.target.value)} /><button className="w-full bg-blue-500 text-white rounded py-2">Login</button><p className="mt-3 text-sm">Don't have an account? <Link className="text-blue-500" to="/register">Register</Link></p></form>;
}
