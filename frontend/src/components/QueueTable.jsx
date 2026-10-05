import PriorityBadge from "./PriorityBadge";

// "5 min ago" from an ISO timestamp. Re-evaluated on every render; the queue
// polls every few seconds, so it stays fresh without its own timer.
function timeAgo(isoString) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(isoString).getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.floor(hours / 24)} d ago`;
}

const HEADERS = ["Priority", "Patient", "Age", "HR (bpm)", "BP (mmHg)", "Temp (°C)", "Confidence", "Arrived"];

function SkeletonRows() {
  return Array.from({ length: 4 }, (_, row) => (
    <tr key={row} className="animate-pulse">
      {HEADERS.map((header) => (
        <td key={header} className="px-4 py-3">
          <div className="h-4 rounded bg-slate-200" />
        </td>
      ))}
    </tr>
  ));
}

export default function QueueTable({ queue, isLoading, error, lastUpdated, onRefresh }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold">Priority queue</h2>
          <p className="text-xs text-slate-500">
            {queue.length} {queue.length === 1 ? "patient" : "patients"}
            {lastUpdated && ` · updated ${lastUpdated.toLocaleTimeString()}`}
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div role="alert" className="border-b border-red-200 bg-red-50 px-5 py-2 text-sm text-red-700">
          {error}
          {queue.length > 0 && " Showing the last data we received."}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {HEADERS.map((header) => (
                <th key={header} scope="col" className="px-4 py-3 font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              <SkeletonRows />
            ) : queue.length === 0 ? (
              <tr>
                <td colSpan={HEADERS.length} className="px-4 py-12 text-center text-slate-500">
                  {error ? "Could not load the queue." : "No patients waiting. Add one using the form."}
                </td>
              </tr>
            ) : (
              queue.map((record) => (
                <tr key={record.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <PriorityBadge priority={record.prediction.predicted_priority} />
                  </td>
                  <td className="px-4 py-3 font-medium">{record.patient_name}</td>
                  <td className="px-4 py-3 tabular-nums">{record.age}</td>
                  <td className="px-4 py-3 tabular-nums">{record.heart_rate}</td>
                  <td className="px-4 py-3 tabular-nums">{record.systolic_bp}</td>
                  <td className="px-4 py-3 tabular-nums">{record.temperature.toFixed(1)}</td>
                  <td className="px-4 py-3 tabular-nums">
                    {Math.round(record.prediction.confidence_score * 100)}%
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-500">{timeAgo(record.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}