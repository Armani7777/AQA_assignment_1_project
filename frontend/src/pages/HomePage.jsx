import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import ProductCard from "../components/ProductCard";

export default function HomePage() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  useEffect(() => {
    api("/api/products/?page_size=8").then((d) => setProducts(d.results || []));
    api("/api/categories/").then(setCategories);
  }, []);
  return (
    <div className="space-y-8">
      <section className="bg-blue-500 text-white rounded p-8"><h1 className="text-3xl font-bold">Discover great products</h1></section>
      <section><h2 className="text-xl font-semibold mb-3">Categories</h2><div className="grid grid-cols-2 md:grid-cols-3 gap-3">{categories.map(c=><div key={c.id} className="bg-white rounded p-4">{c.name}</div>)}</div></section>
      <section><div className="flex justify-between"><h2 className="text-xl font-semibold">Popular products</h2><Link to="/products" className="text-blue-500">See all</Link></div><div className="grid md:grid-cols-4 gap-4 mt-3">{products.map(p=><ProductCard key={p.id} product={p} />)}</div></section>
    </div>
  );
}
