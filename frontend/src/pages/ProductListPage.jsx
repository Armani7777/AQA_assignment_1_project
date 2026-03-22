import { useEffect, useState } from "react";
import { api } from "../api/client";
import CategoryFilter from "../components/CategoryFilter";
import ProductCard from "../components/ProductCard";
import SearchBar from "../components/SearchBar";

export default function ProductListPage() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);

  useEffect(() => { api("/api/categories/").then(setCategories); }, []);
  useEffect(() => {
    const t = setTimeout(async () => {
      const qs = new URLSearchParams({ page, ...(search && { search }), ...(category && { category }) }).toString();
      const data = await api(`/api/products/?${qs}`);
      setItems(data.results || []);
      setNext(data.next);
    }, 300);
    return () => clearTimeout(t);
  }, [search, category, page]);

  return (
    <div className="grid md:grid-cols-4 gap-4">
      <aside className="space-y-3 md:col-span-1"><SearchBar value={search} onChange={setSearch} placeholder="Search products" /><CategoryFilter categories={categories} value={category} onChange={setCategory} /></aside>
      <section className="md:col-span-3"><p className="mb-3">Found: {items.length}</p><div className="grid md:grid-cols-3 gap-4">{items.map(p=><ProductCard key={p.id} product={p} />)}</div><div className="flex gap-2 mt-4"><button disabled={page===1} className="px-3 py-1 border rounded" onClick={()=>setPage(p=>p-1)}>Prev</button><button disabled={!next} className="px-3 py-1 border rounded" onClick={()=>setPage(p=>p+1)}>Next</button></div></section>
    </div>
  );
}
