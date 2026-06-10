import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HiOutlineSparkles,
  HiOutlineLockClosed,
  HiOutlineEnvelope,
  HiArrowRight,
  HiOutlineBolt,
} from "react-icons/hi2";
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
  { label: "Platform Owner", role: "SUPER_ADMIN", merchant: null, email: "super@saleos.com", password: "super1234" },
  { label: "Habesha Coffee — Admin", role: "ADMIN", merchant: "Habesha Coffee", email: "admin@habesha.com", password: "admin1234" },
  { label: "Habesha Coffee — Manager", role: "MANAGER", merchant: "Habesha Coffee", email: "manager@habesha.com", password: "manager1234" },
  { label: "Habesha Coffee — Staff", role: "STAFF", merchant: "Habesha Coffee", email: "staff@habesha.com", password: "staff1234" },
  { label: "Habesha Coffee — Customer", role: "CUSTOMER", merchant: "Habesha Coffee", email: "customer@habesha.com", password: "customer1234" },
  { label: "Buna Roasters — Admin", role: "ADMIN", merchant: "Buna Roasters", email: "admin@buna.com", password: "admin1234" },
];

const ROLE_BADGE: Record<string, string> = {
  SUPER_ADMIN: "bg-purple-100 text-purple-700",
  ADMIN: "bg-brand-100 text-brand-700",
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
    <div className="min-h-screen relative overflow-hidden">
      {/* Ambient background gradient */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-brand-50 via-white to-sky-50" />
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-brand-200/40 rounded-full blur-3xl -z-10" />
      <div className="absolute -bottom-40 -right-32 w-[28rem] h-[28rem] bg-sky-300/30 rounded-full blur-3xl -z-10" />

      <div className="min-h-screen p-4 sm:p-8 flex items-center justify-center">
        <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Login form */}
          <div className="lg:col-span-3 card card-pad sm:p-10 animate-slide-up">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 grid place-items-center text-white shadow-lg">
                <HiOutlineSparkles className="w-6 h-6" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-widest text-brand-700 font-semibold">SaleOS</p>
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 leading-tight">
                  Welcome back
                </h1>
              </div>
            </div>
            <p className="text-sm text-slate-500 mb-8">
              Sign in to your Telegram-first commerce dashboard.
            </p>

            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <label className="label">Email</label>
                <div className="relative">
                  <HiOutlineEnvelope className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input pl-9"
                    placeholder="you@business.com"
                  />
                </div>
              </div>

              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <HiOutlineLockClosed className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input pl-9"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {error && (
                <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2.5">
                  {error}
                </div>
              )}

              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? "Signing in…" : (
                  <>
                    Sign in <HiArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <p className="mt-8 text-sm text-slate-600 text-center">
              New to SaleOS?{" "}
              <Link to="/register" className="text-brand-700 hover:text-brand-800 font-semibold">
                Create a merchant account
              </Link>
            </p>
          </div>

          {/* Right: Sample credentials */}
          <div className="lg:col-span-2 card card-pad animate-slide-up">
            <div className="flex items-center gap-2 mb-1.5">
              <HiOutlineBolt className="w-5 h-5 text-amber-500" />
              <h2 className="section-title">Quick sign-in</h2>
              <span className="badge bg-amber-100 text-amber-800 uppercase tracking-wider">dev</span>
            </div>
            <p className="hint mb-4">
              Click a row to autofill, or hit Login to jump straight in.
            </p>

            <ul className="space-y-2 max-h-[460px] overflow-auto pr-1 scroll-thin">
              {SAMPLE_ACCOUNTS.map((account) => (
                <li
                  key={account.email}
                  className="group border border-slate-200 rounded-xl p-3 hover:border-brand-400 hover:bg-brand-50/40 transition cursor-pointer"
                  onClick={() => fill(account)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-900 truncate text-sm">
                          {account.label}
                        </span>
                        <span
                          className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded-full ${
                            ROLE_BADGE[account.role] ?? "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {account.role}
                        </span>
                      </div>
                      <div className="text-xs text-slate-600 mt-1 font-mono break-all">
                        {account.email}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">
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
                      className="shrink-0 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 transition disabled:opacity-60"
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
