export default function SearchBar({ value, onChange, placeholder = "Search" }) {
  return <input className="border rounded px-3 py-2 w-full" value={value} onChange={(e)=>onChange(e.target.value)} placeholder={placeholder} />;
}
