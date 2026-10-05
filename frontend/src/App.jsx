import QueueTable from "./components/QueueTable";
import TriageForm from "./components/TriageForm";
import { useTriageQueue } from "./hooks/useTriageQueue.js";

export default function App() {
  const { queue, isLoading, error, lastUpdated, refresh } = useTriageQueue();

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <h1 className="text-xl font-bold tracking-tight">Intelligent Patient Triage</h1>
          <span className="flex items-center gap-2 text-xs text-slate-500">
            <span
              className={`h-2 w-2 rounded-full ${error ? "bg-red-500" : "animate-pulse bg-green-500"}`}
              aria-hidden="true"
            />
            {error ? "Offline" : "Live"}
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[22rem_1fr] lg:items-start">
        {/* After a successful submit, refresh the queue right away instead of waiting for the next poll. */}
        <TriageForm onSubmitted={refresh} />
        <QueueTable
          queue={queue}
          isLoading={isLoading}
          error={error}
          lastUpdated={lastUpdated}
          onRefresh={refresh}
        />
      </main>

      <footer className="px-4 pb-8 text-center text-xs text-slate-500">
        Demo project trained on synthetic data. Not for clinical use.
      </footer>
    </div>
  );
}