import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function ProfilePage() {
  const { user, refreshMe } = useAuth();
  const [profile, setProfile] = useState({ full_name: "", phone: "" });
  const [pwd, setPwd] = useState({ old_password: "", new_password: "", confirm: "" });
  useEffect(()=>{ if (user) setProfile({ full_name: user.full_name || "", phone: user.phone || "" }); }, [user]);
  const saveProfile = async (e) => { e.preventDefault(); await api("/api/users/profile/", { method: "PATCH", body: JSON.stringify(profile) }); await refreshMe(); alert("Saved"); };
  const changePassword = async (e) => { e.preventDefault(); if (pwd.new_password !== pwd.confirm) return alert("Passwords mismatch"); await api("/api/users/change-password/", { method: "PUT", body: JSON.stringify({ old_password: pwd.old_password, new_password: pwd.new_password }) }); alert("Password changed"); };
  return <div className="grid md:grid-cols-2 gap-4"><form onSubmit={saveProfile} className="bg-white p-4 rounded"><h2 className="font-semibold">Profile</h2><input className="border rounded p-2 w-full my-2" value={profile.full_name} onChange={(e)=>setProfile({...profile, full_name:e.target.value})} placeholder="Full name" /><input className="border rounded p-2 w-full my-2" value={profile.phone} onChange={(e)=>setProfile({...profile, phone:e.target.value})} placeholder="Phone" />{user?.is_seller && <p className="text-blue-500 text-sm">Seller Account</p>}<button className="bg-blue-500 text-white px-4 py-2 rounded mt-2">Save</button></form><form onSubmit={changePassword} className="bg-white p-4 rounded"><h2 className="font-semibold">Change password</h2><input className="border rounded p-2 w-full my-2" type="password" placeholder="Old password" onChange={(e)=>setPwd({...pwd, old_password:e.target.value})} /><input className="border rounded p-2 w-full my-2" type="password" placeholder="New password" onChange={(e)=>setPwd({...pwd, new_password:e.target.value})} /><input className="border rounded p-2 w-full my-2" type="password" placeholder="Confirm" onChange={(e)=>setPwd({...pwd, confirm:e.target.value})} /><button className="border px-4 py-2 rounded mt-2">Update password</button></form></div>;
}
