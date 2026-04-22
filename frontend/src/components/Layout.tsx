import { Link, Outlet, useLocation } from "react-router-dom";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/queue", label: "Patient Queue" },
  { to: "/patients", label: "Patients" },
  { to: "/alerts", label: "Alerts" },
  { to: "/billing", label: "Billing" }
];

export function Layout() {
  const location = useLocation();
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-slate-900 text-white p-4">
        <h1 className="text-xl font-semibold mb-5">PharmRPM</h1>
        <nav className="space-y-2">
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`block rounded px-3 py-2 text-sm ${
                location.pathname === item.to ? "bg-teal-600" : "hover:bg-slate-700"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
