/** Option icons. A picture is read faster than a sentence, at any age. */
const PATHS = {
  pill: "M10.5 20.5a6 6 0 01-8.5-8.5l9.5-9.5a6 6 0 018.5 8.5l-9.5 9.5zM6.5 8.5l9 9",
  tube: "M9 3h6v4l3 12a2 2 0 01-2 2H8a2 2 0 01-2-2L9 7V3zM7 13h10",
  leaf: "M4 20c0-8 6-14 16-14 0 10-6 15-13 15H4v-1zm3-2c3-4 6-6 9-7",
  drop: "M12 3s6 6.5 6 10.5a6 6 0 11-12 0C6 9.5 12 3 12 3z",
  mineral: "M12 3l7 5-2.5 11h-9L5 8l7-5zM8 8h8",
  none: "M6 12h12",
};

export default function KioskIcon({ name, className = "w-6 h-6" }) {
  const d = PATHS[name];
  if (!d) return null;
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  );
}
