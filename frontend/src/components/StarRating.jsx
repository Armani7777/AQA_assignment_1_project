export default function StarRating({ rating = 0 }) {
  return <span>{"★".repeat(Math.round(rating))}{"☆".repeat(5 - Math.round(rating))}</span>;
}
