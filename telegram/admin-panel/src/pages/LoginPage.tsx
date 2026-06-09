import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login, getMe } from "../lib/authApi";
import { useAuthStore } from "../store/auth";

interface SampleAccount {
  label: string;
  role: string;
  merchant: string | null;
  email: string;
  password: string;
}

const SAMPLE_ACCOUNTS: SampleAccount[] = [
  {
    label: "Platform Owner",
    role: "SUPER_ADMIN",
    merchant: null,
    email: "super@saleos.com",
    password: "super1234",
  },
  {
    label: "Habesha Coffee — Admin",
    role: "ADMIN",
    merchant: "Habesha Coffee",
    email: "admin@habesha.com",
    password: "admin1234",
  },
  {
    label: "Habesha Coffee — Manager",
    role: "MANAGER",
    merchant: "Habesha Coffee",
    email: "manager@habesha.com",
    password: "manager1234",
  },
  {
    label: "Habesha Coffee — Staff",
    role: "STAFF",
    merchant: "Habesha Coffee",
    email: "staff@habesha.com",
    password: "staff1234",
  },
  {
    label: "Habesha Coffee — Customer",
    role: "CUSTOMER",
    merchant: "Habesha Coffee",
    email: "customer@habesha.com",
    password: "customer1234",
  },
  {
    label: "Buna Roasters — Admin",
    role: "ADMIN",
    merchant: "Buna Roasters",
    email: "admin@buna.com",
    password: "admin1234",
  },
];

const ROLE_BADGE: Record<string, string> = {
  SUPER_ADMIN: "bg-purple-100 text-purple-700",
  ADMIN: "bg-brand-50 text-brand-700",
  MANAGER: "bg-amber-100 text-amber-700",
  STAFF: "bg-emerald-100 text-emerald-700",
  CUSTOMER: "bg-slate-100 text-slate-700",
};

export default function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(creds: { email: string; password: string }) {
    setError(null);
    setLoading(true);
    try {
      const tokens = await login(creds);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await getMe();
      setUser(me);
      navigate("/", { replace: true });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? humanize(detail) : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    submit({ email, password });
  }

  function fill(account: SampleAccount) {
    setEmail(account.email);
    setPassword(account.password);
    setError(null);
  }

  function quickLogin(account: SampleAccount) {
    setEmail(account.email);
    setPassword(account.password);
    submit({ email: account.email, password: account.password });
  }

  return (
    <div className="min-h-screen bg-slate-50 p-4 flex items-center justify-center">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Login form */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8">
          <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900 mb-1">
            Sign in to SaleOS
          </h1>
          <p className="text-sm text-slate-500 mb-6">Merchant admin panel</p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                placeholder="you@business.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium py-2.5 transition disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-sm text-slate-600 text-center">
            New to SaleOS?{" "}
            <Link to="/register" className="text-brand-600 hover:text-brand-700 font-medium">
              Create a merchant account
            </Link>
          </p>
        </div>

        {/* Right: Dev credentials */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-lg sm:text-xl font-semibold text-slate-900">
              Sample accounts
            </h2>
            <span className="text-xs uppercase tracking-wide bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
              dev only
            </span>
          </div>
          <p className="text-sm text-slate-500 mb-4">
            Click a row to autofill, or use “Login” to jump straight in.
          </p>

          <ul className="space-y-2 max-h-[460px] overflow-auto pr-1">
            {SAMPLE_ACCOUNTS.map((account) => (
              <li
                key={account.email}
                className="border border-slate-200 rounded-xl p-3 hover:border-brand-400 hover:bg-brand-50/40 transition cursor-pointer"
                onClick={() => fill(account)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-slate-900 truncate">
                        {account.label}
                      </span>
                      <span
                        className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${
                          ROLE_BADGE[account.role] ?? "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {account.role}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 mt-1 font-mono break-all">
                      {account.email}
                    </div>
                    <div className="text-xs text-slate-500 font-mono">
                      pw: {account.password}
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={loading}
                    onClick={(e) => {
                      e.stopPropagation();
                      quickLogin(account);
                    }}
                    className="shrink-0 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 transition disabled:opacity-60"
                  >
                    Login
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function humanize(code: string): string {
  switch (code) {
    case "invalid_credentials":
      return "Wrong email or password.";
    case "user_not_found":
      return "No account found for that email.";
    default:
      return code.replaceAll("_", " ");
  }
}
