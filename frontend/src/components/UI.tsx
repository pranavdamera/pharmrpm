export function StatCard({ title, value, sub }: { title: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="text-sm text-slate-500">{title}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
      {sub ? <div className="text-xs text-slate-500 mt-1">{sub}</div> : null}
    </div>
  );
}

export function Badge({ text, tone }: { text: string; tone: "green" | "yellow" | "red" | "slate" | "blue" }) {
  const styles = {
    green: "bg-emerald-100 text-emerald-800",
    yellow: "bg-amber-100 text-amber-800",
    red: "bg-rose-100 text-rose-800",
    slate: "bg-slate-100 text-slate-700",
    blue: "bg-blue-100 text-blue-800"
  };
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[tone]}`}>{text}</span>;
}
