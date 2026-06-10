import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  HiOutlineSparkles,
  HiArrowRight,
  HiOutlineBuildingStorefront,
  HiOutlineUser,
} from "react-icons/hi2";
import { register, getMe } from "../lib/authApi";
import { useAuthStore } from "../store/auth";

export default function RegisterPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const [form, setForm] = useState({
    business_name: "",
    contact_phone: "",
    contact_email: "",
    first_name: "",
    last_name: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await register(form);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await getMe();
      setUser(me);
      navigate("/", { replace: true });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? humanize(detail) : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-brand-50 via-white to-sky-50" />
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-brand-200/40 rounded-full blur-3xl -z-10" />
      <div className="absolute -bottom-40 -right-32 w-[28rem] h-[28rem] bg-sky-300/30 rounded-full blur-3xl -z-10" />

      <div className="min-h-screen flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-2xl card card-pad sm:p-10 animate-slide-up">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 grid place-items-center text-white shadow-lg">
              <HiOutlineSparkles className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-widest text-brand-700 font-semibold">SaleOS</p>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 leading-tight">
                Create your account
              </h1>
            </div>
          </div>
          <p className="text-sm text-slate-500 mb-7">
            Spin up your merchant workspace. You'll be the first admin.
          </p>

          <form onSubmit={onSubmit} className="space-y-5">
            <Section title="Your business" Icon={HiOutlineBuildingStorefront}>
              <Field label="Business name" required>
                <input
                  required
                  minLength={2}
                  className="input"
                  value={form.business_name}
                  onChange={(e) => update("business_name", e.target.value)}
                  placeholder="Habesha Coffee"
                />
              </Field>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Business phone" required>
                  <input
                    required
                    type="tel"
                    className="input"
                    value={form.contact_phone}
                    onChange={(e) => update("contact_phone", e.target.value)}
                    placeholder="+251911000000"
                  />
                </Field>
                <Field label="Business email" required>
                  <input
                    required
                    type="email"
                    className="input"
                    value={form.contact_email}
                    onChange={(e) => update("contact_email", e.target.value)}
                    placeholder="you@business.com"
                  />
                </Field>
              </div>
            </Section>

            <Section title="About you" Icon={HiOutlineUser}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="First name" required>
                  <input
                    required
                    className="input"
                    value={form.first_name}
                    onChange={(e) => update("first_name", e.target.value)}
                  />
                </Field>
                <Field label="Last name" required>
                  <input
                    required
                    className="input"
                    value={form.last_name}
                    onChange={(e) => update("last_name", e.target.value)}
                  />
                </Field>
              </div>
              <Field label="Password" required>
                <input
                  required
                  type="password"
                  minLength={8}
                  autoComplete="new-password"
                  className="input"
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  placeholder="At least 8 characters"
                />
              </Field>
            </Section>

            {error && (
              <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2.5">
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "Creating account…" : (
                <>
                  Create account <HiArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-7 text-sm text-slate-600 text-center">
            Already have an account?{" "}
            <Link to="/login" className="text-brand-700 hover:text-brand-800 font-semibold">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  Icon,
  children,
}: {
  title: string;
  Icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-3.5">
      <div className="flex items-center gap-2 text-slate-700">
        <Icon className="w-4 h-4 text-brand-600" />
        <h3 className="text-xs font-semibold uppercase tracking-wider">{title}</h3>
      </div>
      <div className="space-y-3.5">{children}</div>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="label">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

function humanize(code: string): string {
  switch (code) {
    case "email_already_registered":
    case "merchant_email_already_registered":
      return "That email is already in use.";
    case "phone_already_registered":
    case "merchant_phone_already_registered":
      return "That phone number is already in use.";
    default:
      return code.replaceAll("_", " ");
  }
}
