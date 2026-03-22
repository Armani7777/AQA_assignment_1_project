import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const CartContext = createContext(null);
export const useCart = () => useContext(CartContext);

export function CartProvider({ children }) {
  const [cart, setCart] = useState({ items: [] });

  const refreshCart = async () => {
    try { setCart(await api("/api/cart/")); } catch { setCart({ items: [] }); }
  };

  useEffect(() => { if (localStorage.getItem("access")) refreshCart(); }, []);

  return <CartContext.Provider value={{ cart, setCart, refreshCart }}>{children}</CartContext.Provider>;
}
