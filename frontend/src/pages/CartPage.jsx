import { Link, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { api } from "../api/client";
import { useCart } from "../context/CartContext";

export default function CartPage() {
  const { cart, refreshCart } = useCart();
  const navigate = useNavigate();
  useEffect(() => { refreshCart(); }, []);

  const changeQty = async (id, quantity) => { await api(`/api/cart/items/${id}/`, { method: "PUT", body: JSON.stringify({ quantity }) }); refreshCart(); };
  const remove = async (id) => { await api(`/api/cart/items/${id}/`, { method: "DELETE" }); refreshCart(); };
  const applyCoupon = async () => {
    const code = prompt("Coupon code");
    if (!code) return;
    await api("/api/cart/apply-coupon/", { method: "POST", body: JSON.stringify({ code }) });
    refreshCart();
  };

  return <div className="grid md:grid-cols-3 gap-4"><div className="md:col-span-2 space-y-2">{(cart.items||[]).map(i=><div key={i.id} className="bg-white rounded p-3 flex justify-between"><div>{i.product_title} - ${i.product_price}</div><div className="flex gap-2"><button onClick={()=>changeQty(i.id, Math.max(1, i.quantity-1))}>-</button><span>{i.quantity}</span><button onClick={()=>changeQty(i.id, i.quantity+1)}>+</button><button className="text-red-500" onClick={()=>remove(i.id)}>Delete</button></div></div>)}</div><aside className="bg-white p-4 rounded"><p>Subtotal: ${cart.subtotal || 0}</p><p>Discount: ${cart.discount || 0}</p><p className="font-bold">Total: ${cart.total || 0}</p><button className="w-full border rounded py-2 mt-2" onClick={applyCoupon}>Apply Coupon</button><button disabled={!cart.items?.length} className="w-full bg-blue-500 text-white rounded py-2 mt-2 disabled:opacity-50" onClick={()=>navigate('/checkout')}>Proceed to Checkout</button><Link to="/products" className="text-blue-500 text-sm inline-block mt-2">Continue shopping</Link></aside></div>;
}
