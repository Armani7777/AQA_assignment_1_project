import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const [form, setForm] = useState({ username: "", email: "", password: "", confirm: "", full_name: "", is_seller: false });
  const [error, setError] = useState("");
  const { register } = useAuth();
  const navigate = useNavigate();
  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) return setError("Passwords do not match");
    try { await register(form); navigate("/"); } catch { setError("Registration failed"); }
  };
  return <form onSubmit={submit} className="max-w-md mx-auto bg-white p-6 rounded"><h1 className="text-xl font-semibold mb-4">Register</h1>{error && <p className="text-red-500 mb-2">{error}</p>}<input className="border rounded p-2 w-full mb-2" placeholder="Username" value={form.username} onChange={(e)=>setForm({...form, username:e.target.value})} /><input className="border rounded p-2 w-full mb-2" placeholder="Email" value={form.email} onChange={(e)=>setForm({...form, email:e.target.value})} /><input className="border rounded p-2 w-full mb-2" type="password" placeholder="Password" value={form.password} onChange={(e)=>setForm({...form, password:e.target.value})} /><input className="border rounded p-2 w-full mb-2" type="password" placeholder="Confirm Password" value={form.confirm} onChange={(e)=>setForm({...form, confirm:e.target.value})} /><input className="border rounded p-2 w-full mb-2" placeholder="Full name" value={form.full_name} onChange={(e)=>setForm({...form, full_name:e.target.value})} /><label className="text-sm flex gap-2 items-center"><input type="checkbox" checked={form.is_seller} onChange={(e)=>setForm({...form, is_seller:e.target.checked})} />Register as Seller</label><button className="w-full bg-blue-500 text-white rounded py-2 mt-3">Register</button><p className="mt-3 text-sm">Already have an account? <Link className="text-blue-500" to="/login">Login</Link></p></form>;
}
