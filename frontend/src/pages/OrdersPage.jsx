import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  useEffect(()=>{api("/api/orders/").then((d)=>setOrders(d.results || []));},[]);
  return <div className="bg-white rounded p-4"><h1 className="text-xl font-semibold mb-3">My Orders</h1><div className="space-y-2">{orders.map(o=><Link key={o.id} to={`/orders/${o.id}`} className="block border rounded p-3">#{o.id} - {o.status} - ${o.total_price}</Link>)}</div></div>;
}
