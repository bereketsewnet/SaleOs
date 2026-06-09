import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
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
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl p-6 sm:p-8">
        <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900 mb-1">
          Create your merchant account
        </h1>
        <p className="text-sm text-slate-500 mb-6">
          You'll be the first admin of this business.
        </p>

        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Business name" required>
            <input
              required
              minLength={2}
              className={inputClass}
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
                className={inputClass}
                value={form.contact_phone}
                onChange={(e) => update("contact_phone", e.target.value)}
                placeholder="+251911000000"
              />
            </Field>
            <Field label="Business email" required>
              <input
                required
                type="email"
                className={inputClass}
                value={form.contact_email}
                onChange={(e) => update("contact_email", e.target.value)}
                placeholder="you@business.com"
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="First name" required>
              <input
                required
                className={inputClass}
                value={form.first_name}
                onChange={(e) => update("first_name", e.target.value)}
              />
            </Field>
            <Field label="Last name" required>
              <input
                required
                className={inputClass}
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
              className={inputClass}
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              placeholder="At least 8 characters"
            />
          </Field>

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
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-slate-600 text-center">
          Already have an account?{" "}
          <Link to="/login" className="text-brand-600 hover:text-brand-700 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500";

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
      <label className="block text-sm font-medium text-slate-700 mb-1">
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
