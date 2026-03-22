export default function CategoryFilter({ categories, value, onChange }) {
  return (
    <select className="border rounded px-3 py-2 w-full" value={value} onChange={(e)=>onChange(e.target.value)}>
      <option value="">All categories</option>
      {categories.map((c)=><option key={c.id} value={c.id}>{c.name}</option>)}
    </select>
  );
}
