// Full class names are written out (not built from strings) so Tailwind can find them.
const STYLES = {
  Critical: { badge: "bg-red-100 text-red-800 ring-red-600/20", dot: "bg-red-600" },
  Urgent: { badge: "bg-amber-100 text-amber-800 ring-amber-600/20", dot: "bg-amber-500" },
  Standard: { badge: "bg-green-100 text-green-800 ring-green-600/20", dot: "bg-green-600" },
};

const FALLBACK = { badge: "bg-slate-100 text-slate-700 ring-slate-500/20", dot: "bg-slate-500" };

export default function PriorityBadge({ priority }) {
  const style = STYLES[priority] ?? FALLBACK;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${style.badge}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} aria-hidden="true" />
      {priority}
    </span>
  );
}