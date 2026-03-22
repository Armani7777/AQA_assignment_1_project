import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function CheckoutPage() {
  const [shipping_address, setAddress] = useState("");
  const navigate = useNavigate();
  const submit = async (e) => {
    e.preventDefault();
    const order = await api("/api/orders/", { method: "POST", body: JSON.stringify({ shipping_address }) });
    navigate(`/orders/${order.id}`);
  };
  return <form onSubmit={submit} className="bg-white p-4 rounded max-w-xl space-y-3"><h1 className="text-xl font-semibold">Checkout</h1><textarea className="w-full border rounded p-2" rows="4" placeholder="Shipping address" value={shipping_address} onChange={(e)=>setAddress(e.target.value)} required /><button className="bg-blue-500 text-white px-4 py-2 rounded">Place Order</button></form>;
}
