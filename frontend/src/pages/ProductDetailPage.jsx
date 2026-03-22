import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import StarRating from "../components/StarRating";

export default function ProductDetailPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [qty, setQty] = useState(1);

  useEffect(() => {
    api(`/api/products/${id}/`).then(setProduct);
    api(`/api/reviews/?product=${id}`).then((d)=>setReviews(d.results || d));
  }, [id]);

  const addToCart = async () => {
    await api("/api/cart/items/", { method: "POST", body: JSON.stringify({ product_id: Number(id), quantity: qty }) });
    alert("Added to cart");
  };

  if (!product) return <p>Loading...</p>;
  return <div className="grid md:grid-cols-2 gap-6"><img src={product.image_url || "https://via.placeholder.com/400x300"} alt={product.title} className="w-full rounded" /><div><h1 className="text-2xl font-bold">{product.title}</h1><p className="text-blue-500 text-xl mt-2">${product.price}</p><p className="mt-2">In stock: {product.stock}</p><p className="mt-3">{product.description}</p><div className="flex gap-2 mt-4"><input type="number" min="1" value={qty} onChange={(e)=>setQty(Number(e.target.value))} className="border rounded px-2 w-20" /><button className="bg-blue-500 text-white px-4 py-2 rounded" onClick={addToCart}>Add to Cart</button></div><p className="mt-4"><StarRating rating={product.average_rating} /> ({product.reviews_count})</p></div><div className="md:col-span-2"><h2 className="font-semibold">Reviews</h2>{reviews.map(r=><div key={r.id} className="bg-white p-3 rounded mt-2"><p className="font-medium">{r.user_name}</p><p>{"★".repeat(r.rating)}</p><p>{r.comment}</p></div>)}</div></div>;
}
