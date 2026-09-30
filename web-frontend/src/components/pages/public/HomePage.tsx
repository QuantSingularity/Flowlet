import {
  ArrowRight,
  CheckCircle,
  CreditCard,
  Globe,
  Shield,
  TrendingUp,
  Wallet,
  Zap,
  Menu,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: Wallet,
    title: "Digital Wallets",
    description:
      "Seamlessly manage multi-currency digital wallets with real-time balance tracking and instant transfers.",
    color: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
  {
    icon: CreditCard,
    title: "Card Issuance",
    description:
      "Issue virtual and physical cards instantly with comprehensive spend controls and limits.",
    color: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
  },
  {
    icon: Shield,
    title: "Bank-Grade Security",
    description:
      "Enterprise-level encryption, fraud detection, and compliance built into every transaction.",
    color: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  },
  {
    icon: Zap,
    title: "Instant Payments",
    description:
      "Send and receive payments instantly with low fees and 150+ supported payment methods.",
    color: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  },
  {
    icon: Globe,
    title: "Global Reach",
    description:
      "Support for 50+ currencies with competitive FX rates and international transaction coverage.",
    color: "bg-pink-500/10 text-pink-600 dark:text-pink-400",
  },
  {
    icon: TrendingUp,
    title: "Analytics & Insights",
    description:
      "Track spending patterns, get actionable insights, and forecast your financial health.",
    color: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400",
  },
];

const benefits = [
  "KYC/AML Compliance Built-in",
  "PCI-DSS Certified Infrastructure",
  "Real-time Transaction Monitoring",
  "Advanced AI Fraud Detection",
  "Multi-factor Authentication",
  "99.99% Uptime SLA",
];

const stats = [
  { label: "Transactions/day", value: "2M+" },
  { label: "Countries supported", value: "150+" },
  { label: "API uptime", value: "99.99%" },
  { label: "Setup time", value: "< 1 day" },
];

export default function HomePage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Navbar ── */}
      <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4">
          <nav className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center shadow-sm">
                <span className="text-white font-bold text-sm">F</span>
              </div>
              <span className="text-xl font-semibold tracking-tight text-foreground">
                Flowlet
              </span>
            </div>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center gap-6 text-sm">
              <Link
                to="/payments"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Payments
              </Link>
              <Link
                to="/compliance"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Compliance
              </Link>
              <Link
                to="/developer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Developers
              </Link>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2">
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Sign in
                  </Button>
                </Link>
                <Link to="/register">
                  <Button
                    size="sm"
                    className="gap-1.5 bg-gradient-brand hover:opacity-90 transition-opacity"
                  >
                    Get started
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>

              {/* Mobile hamburger */}
              <button
                className="md:hidden h-9 w-9 flex items-center justify-center rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <X className="h-4 w-4" />
                ) : (
                  <Menu className="h-4 w-4" />
                )}
              </button>
            </div>
          </nav>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="md:hidden pt-4 pb-2 border-t border-border/40 mt-4 space-y-1">
              <Link
                to="/payments"
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Payments
              </Link>
              <Link
                to="/compliance"
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Compliance
              </Link>
              <Link
                to="/developer"
                className="block px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Developers
              </Link>
              <div className="flex gap-2 pt-2">
                <Link to="/login" className="flex-1">
                  <Button variant="outline" size="sm" className="w-full">
                    Sign in
                  </Button>
                </Link>
                <Link to="/register" className="flex-1">
                  <Button
                    size="sm"
                    className="w-full bg-gradient-brand hover:opacity-90"
                  >
                    Get started
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="container mx-auto px-6 py-24 text-center">
        <Badge
          variant="secondary"
          className="mb-6 gap-1.5 px-3 py-1 text-xs font-medium"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          Now in production · 200+ companies
        </Badge>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight leading-tight text-foreground">
          Embedded Finance
          <br />
          <span className="text-gradient">for Modern Builders</span>
        </h1>
        <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
          Integrate wallets, payments, and cards into your product in days - not
          months. Built for developers. Trusted by enterprises.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/register">
            <Button
              size="lg"
              className="gap-2 px-8 bg-gradient-brand hover:opacity-90 transition-opacity shadow-md"
            >
              Start building free
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link to="/developer">
            <Button size="lg" variant="outline" className="gap-2 px-8">
              View docs
            </Button>
          </Link>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap items-center justify-center gap-8 mt-16 pt-8 border-t border-border/50">
          {stats.map((item) => (
            <div key={item.label} className="text-center">
              <p className="text-2xl font-bold text-foreground">{item.value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {item.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="container mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold mb-4 tracking-tight text-foreground">
            Everything you need
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            A complete suite of financial services that integrates seamlessly
            into your stack.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group p-6 rounded-2xl border border-border bg-card hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5 transition-all duration-200 card-hover"
              >
                <div
                  className={`w-11 h-11 rounded-xl ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold mb-2 text-card-foreground">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Compliance / Security strip ── */}
      <section className="container mx-auto px-6 py-20">
        <div
          className="rounded-3xl p-10 md:p-16"
          style={{ background: "hsl(var(--sidebar-background))" }}
        >
          <div className="max-w-3xl mx-auto">
            <h2
              className="text-3xl font-bold mb-3 tracking-tight"
              style={{ color: "hsl(var(--sidebar-foreground))" }}
            >
              Compliance & security, built in
            </h2>
            <p
              className="mb-10"
              style={{ color: "hsl(var(--sidebar-foreground) / 0.6)" }}
            >
              We handle the regulatory complexity so you can focus on your
              product.
            </p>
            <div className="grid sm:grid-cols-2 gap-4">
              {benefits.map((benefit) => (
                <div key={benefit} className="flex items-center gap-3">
                  <CheckCircle
                    className="h-4 w-4 shrink-0"
                    style={{ color: "hsl(var(--sidebar-primary))" }}
                  />
                  <span
                    className="text-sm"
                    style={{ color: "hsl(var(--sidebar-foreground) / 0.8)" }}
                  >
                    {benefit}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="container mx-auto px-6 py-20 text-center">
        <div className="rounded-3xl border-2 border-primary/20 bg-primary/5 p-12 md:p-16">
          <h2 className="text-3xl font-bold mb-4 tracking-tight text-foreground">
            Ready to build?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
            Join hundreds of companies using Flowlet to embed financial services
            into their products.
          </p>
          <Link to="/register">
            <Button
              size="lg"
              className="gap-2 px-10 bg-gradient-brand hover:opacity-90 transition-opacity shadow-md"
            >
              Get started free
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-border">
        <div className="container mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-brand flex items-center justify-center">
              <span className="text-white font-bold text-xs">F</span>
            </div>
            <span className="font-medium text-sm text-foreground">Flowlet</span>
          </div>
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Flowlet, Inc. All rights reserved.
          </p>
          <div className="flex gap-4 text-xs text-muted-foreground">
            <Link
              to="/compliance"
              className="hover:text-foreground transition-colors"
            >
              Privacy
            </Link>
            <Link
              to="/compliance"
              className="hover:text-foreground transition-colors"
            >
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
