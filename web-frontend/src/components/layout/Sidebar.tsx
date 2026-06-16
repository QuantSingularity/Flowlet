import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  AlertTriangle,
  BarChart3,
  Bot,
  CreditCard,
  GitBranch,
  Home,
  MessageSquare,
  PiggyBank,
  Settings,
  Shield,
  Wallet,
  X,
  Zap,
  ChevronRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface SidebarProps {
  isOpen: boolean;
  isMobile: boolean;
  onClose: () => void;
}

interface NavItem {
  icon: React.ElementType;
  label: string;
  path: string;
  badge?: string;
  badgeVariant?: "default" | "secondary" | "destructive" | "outline";
}

interface NavGroup {
  title?: string;
  items: NavItem[];
}

const navigation: NavGroup[] = [
  {
    items: [{ icon: Home, label: "Dashboard", path: "/dashboard" }],
  },
  {
    title: "Finance",
    items: [
      { icon: Wallet, label: "Wallet", path: "/wallet" },
      { icon: CreditCard, label: "Cards", path: "/cards" },
      { icon: BarChart3, label: "Analytics", path: "/analytics" },
      { icon: PiggyBank, label: "Budgeting", path: "/financial-planning" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { icon: Bot, label: "AI Assistant", path: "/chat", badge: "AI" },
      {
        icon: AlertTriangle,
        label: "Fraud Alerts",
        path: "/alerts",
        badge: "3",
        badgeVariant: "destructive",
      },
      { icon: Zap, label: "Fraud Detection", path: "/fraud-detection" },
    ],
  },
  {
    title: "Platform",
    items: [
      { icon: GitBranch, label: "Workflows", path: "/workflows" },
      { icon: Shield, label: "Security", path: "/security" },
      { icon: MessageSquare, label: "Compliance", path: "/compliance" },
    ],
  },
  {
    items: [{ icon: Settings, label: "Settings", path: "/settings" }],
  },
];

const SidebarNavItem: React.FC<{
  item: NavItem;
  isActive: boolean;
  onClick?: () => void;
}> = ({ item, isActive, onClick }) => {
  const Icon = item.icon;
  return (
    <Link
      to={item.path}
      onClick={onClick}
      className={cn(
        "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
        isActive
          ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0 transition-transform duration-150",
          isActive ? "scale-110" : "group-hover:scale-105",
        )}
      />
      <span className="flex-1 truncate">{item.label}</span>
      {item.badge && (
        <Badge
          variant={item.badgeVariant ?? "secondary"}
          className={cn(
            "h-5 min-w-[1.25rem] rounded-md px-1.5 text-[10px] font-semibold",
            item.badgeVariant === "destructive"
              ? ""
              : isActive
                ? "bg-white/20 text-white hover:bg-white/20"
                : "bg-sidebar-accent text-sidebar-foreground/70",
          )}
        >
          {item.badge}
        </Badge>
      )}
      {isActive && <ChevronRight className="h-3.5 w-3.5 shrink-0 opacity-60" />}
    </Link>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, isMobile, onClose }) => {
  const location = useLocation();

  const sidebarContent = (
    <div
      className="flex h-full flex-col"
      style={{ background: "hsl(var(--sidebar-background))" }}
    >
      {/* Logo */}
      <div className="flex h-16 shrink-0 items-center justify-between px-5 border-b border-sidebar-border/60">
        <Link
          to="/dashboard"
          className="flex items-center gap-2.5"
          onClick={isMobile ? onClose : undefined}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-brand shadow-md">
            <span className="text-sm font-extrabold text-white tracking-tight">
              F
            </span>
          </div>
          <span className="text-[15px] font-semibold text-sidebar-foreground tracking-tight">
            Flowlet
          </span>
        </Link>
        {isMobile && (
          <button
            onClick={onClose}
            aria-label="Close sidebar"
            className="rounded-lg p-1.5 text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-5">
          {navigation.map((group, gi) => (
            <div key={gi}>
              {group.title && (
                <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-widest text-sidebar-foreground/35">
                  {group.title}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <SidebarNavItem
                    key={item.path}
                    item={item}
                    isActive={
                      item.path === "/dashboard"
                        ? location.pathname === "/dashboard"
                        : location.pathname.startsWith(item.path)
                    }
                    onClick={isMobile ? onClose : undefined}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* Bottom */}
      <div className="shrink-0 px-3 pb-4 border-t border-sidebar-border/60 pt-3">
        <div className="rounded-xl bg-sidebar-accent/60 px-3 py-2.5">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-400 pulse-dot" />
            <span className="text-xs text-sidebar-foreground/60">
              All systems operational
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        {isOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />
        )}
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-50 w-64 shadow-2xl transition-transform duration-300 ease-in-out",
            isOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          {sidebarContent}
        </aside>
      </>
    );
  }

  return (
    <aside
      className={cn(
        "hidden lg:flex lg:flex-col lg:shrink-0 border-r border-sidebar-border/40 transition-all duration-300 ease-out overflow-hidden",
        isOpen ? "lg:w-64" : "w-0",
      )}
    >
      {sidebarContent}
    </aside>
  );
};

export default Sidebar;
