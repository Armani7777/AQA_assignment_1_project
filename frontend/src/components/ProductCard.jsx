import { Link } from "react-router-dom";

export default function ProductCard({ product }) {
  return (
    <div className="bg-white rounded shadow p-4">
      <img src={product.image_url || "https://via.placeholder.com/320x200"} alt={product.title} className="w-full h-40 object-cover rounded" />
      <h3 className="font-semibold mt-3">{product.title}</h3>
      <p className="text-blue-500 font-bold mt-1">${product.price}</p>
      <Link to={`/products/${product.id}`} className="inline-block mt-3 text-sm text-blue-500">View details</Link>
    </div>
  );
}
