import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";

export default function OrderDetailPage() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const load = () => api(`/api/orders/${id}/`).then(setOrder);
  useEffect(() => { load(); }, [id]);
  const cancel = async () => { await api(`/api/orders/${id}/cancel/`, { method: "POST" }); load(); };
  if (!order) return <p>Loading...</p>;
  return <div className="bg-white rounded p-4"><h1 className="text-xl font-semibold">Order #{order.id}</h1><p>Status: {order.status}</p><p className="mt-1">Address: {order.shipping_address}</p><div className="mt-3 space-y-2">{order.items.map(i=><div key={i.id}>{i.product_title} x{i.quantity} - ${i.price}</div>)}</div><p className="font-bold mt-3">Total: ${order.total_price}</p>{order.status === "pending" && <button className="mt-3 border px-3 py-1 rounded" onClick={cancel}>Cancel Order</button>}</div>;
}
