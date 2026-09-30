import { zodResolver } from "@hookform/resolvers/zod";
import {
  Eye,
  EyeOff,
  Loader2,
  ShieldCheck,
  Zap,
  TrendingUp,
} from "lucide-react";
import React, { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppDispatch } from "@/hooks/redux";
import { loginUser } from "@/store/authSlice";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});
type LoginFormData = z.infer<typeof loginSchema>;

const features = [
  {
    icon: ShieldCheck,
    title: "Bank-grade security",
    desc: "AES-256 encryption & MFA",
  },
  { icon: Zap, title: "Instant transfers", desc: "Move money in seconds" },
  {
    icon: TrendingUp,
    title: "AI-powered insights",
    desc: "Smarter financial decisions",
  },
];

const LoginScreen: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "demo@flowlet.com",
      password: "demo123",
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      await dispatch(loginUser(data)).unwrap();
      toast.success("Welcome back!");
      navigate("/dashboard");
    } catch (error: unknown) {
      setError("root", {
        message: typeof error === "string" ? error : "Login failed",
      });
      toast.error("Login failed. Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-mesh">
      {/* ── Left panel ── */}
      <div
        className="hidden lg:flex lg:w-[52%] flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: "hsl(var(--sidebar-background))" }}
      >
        {/* Background orbs */}
        <div
          className="absolute -top-32 -left-32 h-96 w-96 rounded-full opacity-20"
          style={{
            background:
              "radial-gradient(circle, hsl(var(--primary)) 0%, transparent 70%)",
          }}
        />
        <div
          className="absolute -bottom-24 -right-24 h-80 w-80 rounded-full opacity-15"
          style={{
            background:
              "radial-gradient(circle, hsl(250 80% 75%) 0%, transparent 70%)",
          }}
        />

        {/* Logo */}
        <div className="relative flex items-center gap-3 z-10">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-brand shadow-lg">
            <span className="text-lg font-extrabold text-white">F</span>
          </div>
          <span className="text-xl font-semibold text-white tracking-tight">
            Flowlet
          </span>
        </div>

        {/* Hero text */}
        <div className="relative z-10 space-y-10">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3.5 py-1.5 text-xs font-medium text-white/80">
              <div className="h-1.5 w-1.5 rounded-full bg-green-400 pulse-dot" />
              Embedded Finance Platform
            </div>
            <h1 className="text-5xl font-bold text-white leading-[1.12] tracking-tight">
              The future of <span className="text-gradient">embedded</span>
              <br />
              finance is here
            </h1>
            <p className="text-base text-white/55 leading-relaxed max-w-sm">
              Build, scale and manage financial products with the infrastructure
              trusted by modern fintech teams.
            </p>
          </div>

          {/* Feature pills */}
          <div className="space-y-3">
            {features.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="flex items-center gap-4 rounded-2xl bg-white/8 px-4 py-3.5 backdrop-blur-sm border border-white/8"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-brand/80">
                  <Icon className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{title}</p>
                  <p className="text-xs text-white/50">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Social proof */}
          <div className="flex items-center gap-6">
            {[
              ["50K+", "Developers"],
              ["$2B+", "Processed"],
              ["99.99%", "Uptime"],
            ].map(([val, label]) => (
              <div key={label}>
                <p className="text-2xl font-bold text-white tabular-nums">
                  {val}
                </p>
                <p className="text-xs text-white/45 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right panel - form ── */}
      <div className="flex flex-1 items-center justify-center px-6 py-12 lg:px-12">
        <div className="w-full max-w-[400px] animate-fade-in-up">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-brand shadow-md">
              <span className="text-sm font-extrabold text-white">F</span>
            </div>
            <span className="text-lg font-semibold tracking-tight">
              Flowlet
            </span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight">Welcome back</h2>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-4"
            noValidate
          >
            {errors.root && (
              <Alert variant="destructive" className="animate-fade-in">
                <AlertDescription>{errors.root.message}</AlertDescription>
              </Alert>
            )}

            {/* Email */}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">
                Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                className={`h-10 ${errors.email ? "border-destructive focus-visible:ring-destructive" : ""}`}
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium">
                  Password
                </Label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-primary hover:underline underline-offset-4"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className={`h-10 pr-10 ${errors.password ? "border-destructive" : ""}`}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Remember me */}
            <div className="flex items-center gap-2.5 pt-1">
              <Controller
                name="rememberMe"
                control={control}
                render={({ field }) => (
                  <Checkbox
                    id="rememberMe"
                    checked={field.value ?? false}
                    onCheckedChange={field.onChange}
                    className="h-4 w-4"
                  />
                )}
              />
              <Label
                htmlFor="rememberMe"
                className="text-sm font-normal text-muted-foreground cursor-pointer"
              >
                Keep me signed in
              </Label>
            </div>

            <Button
              type="submit"
              className="w-full h-10 bg-gradient-brand hover:opacity-90 transition-opacity shadow-md"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="font-medium text-primary hover:underline underline-offset-4"
            >
              Create account
            </Link>
          </p>

          {/* Demo hint */}
          <div className="mt-6 rounded-xl border border-border/60 bg-secondary/40 px-4 py-3 text-center">
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">
                Demo credentials
              </span>
              {" · "}
              <span>demo@flowlet.com</span>
              {" / demo123"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
