# Flowlet Web Frontend

A modern, enterprise-grade embedded finance platform UI built with React 19, TypeScript, Redux Toolkit, and Tailwind CSS v4.

## Directory Structure

```
flowlet-frontend/
├── src/                          # All application source code
│   ├── components/
│   │   ├── auth/                 # Auth screens (Login, Register, etc.)
│   │   ├── features/             # Feature-based components
│   │   │   ├── dashboard/        # Dashboard & wallet summary
│   │   │   ├── wallet/           # Wallet management
│   │   │   ├── cards/            # Card issuance & management
│   │   │   ├── transactions/     # Send/receive/history
│   │   │   ├── analytics/        # Charts & financial insights
│   │   │   ├── budgeting/        # Budget tracking & savings goals
│   │   │   ├── ai/               # AI chat, fraud detection
│   │   │   ├── security/         # Security settings & monitoring
│   │   │   ├── settings/         # User preferences
│   │   │   ├── compliance/       # GDPR, audit trail, PCI
│   │   │   └── workflow/         # Workflow designer
│   │   ├── layout/               # Header, Sidebar, Layout, ErrorBoundary
│   │   ├── pages/
│   │   │   └── public/           # Public-facing marketing pages
│   │   └── ui/                   # Shadcn/Radix UI primitives
│   ├── config/                   # App constants & configuration
│   ├── hooks/                    # Custom React hooks
│   ├── lib/
│   │   ├── api/                  # API client, authService, walletService
│   │   └── utils/                # Utilities, formatters, validation
│   ├── services/                 # Mock/data services
│   ├── store/                    # Redux store & slices
│   ├── styles/                   # Global CSS (design tokens, animations)
│   ├── tests/
│   │   ├── unit/                 # Pure unit tests
│   │   ├── integration/          # Integration tests
│   │   └── components/           # Component render tests
│   └── types/                    # TypeScript interfaces & types
├── components/ui/                # (Legacy) Shadcn components
├── lib/utils.ts                  # Re-exports from src/lib/utils
├── App.tsx                       # Root component
├── main.tsx                      # Entry point
├── index.html                    # HTML shell with DM Sans font
├── vite.config.ts
├── vitest.config.ts
└── tsconfig.json
```

## Getting Started

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Run tests
pnpm test

# Run tests with UI
pnpm test:ui

# Run tests with coverage
pnpm test:coverage

# Type check
pnpm type-check

# Build for production
pnpm build
```

## Demo Login

| Field    | Value            |
| -------- | ---------------- |
| Email    | demo@flowlet.com |
| Password | demo123          |

## Bug Fixes Applied

1. **Missing `/forgot-password` route** - Added `ForgotPasswordScreen` and route in `AppInner.tsx`
2. **Checkbox + react-hook-form** - Replaced `{...register()}` with `<Controller>` for Radix-based checkboxes in Login & Register
3. **SendMoney amount coercion** - Changed `z.number()` to `z.coerce.number()` so string HTML input values parse correctly
4. **Demo mode without backend** - `authService` now detects demo credentials and bypasses the API
5. **Hardcoded copyright year** - Dynamic `new Date().getFullYear()` in HomePage/Footer
6. **`WalletSummary` trend color** - Expenses "down" is now correctly contextual (not always red)
7. **`TransactionList` missing navigation** - "View all" button now routes to `/wallet/transactions`
8. **Dashboard quick actions** - All buttons now navigate to correct routes
9. **`validateToken` rejected** - Logout path always clears state even when rejected
10. **System theme media query listener** - Added listener cleanup for system theme preference changes
11. **`rootElement` null guard** - `main.tsx` now throws clearly if `#root` is missing
12. **Token expiry buffer** - Token considered expired 5 min before actual expiry

## Architecture Decisions

- **Feature-based structure** - Components organized by domain, not by type
- **Absolute imports** - All imports use `@/` alias for clarity
- **Demo mode** - Full UI works without a backend using demo credentials
- **Optimistic UI** - Forms show immediate feedback without waiting for API
- **CSS custom properties** - Design tokens in `globals.css` enable consistent theming
