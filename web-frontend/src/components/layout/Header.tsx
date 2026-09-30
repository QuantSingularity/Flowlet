import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, LogOut, Menu, Monitor, Search, User, X } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import { useAuth } from "@/hooks/useAuth";
import { logoutUser } from "@/store/authSlice";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onMenuClick: () => void;
  isMobile: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, isMobile }) => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { unreadNotifications } = useAppSelector((state) => state.ui);
  const [searchOpen, setSearchOpen] = useState(false);

  const handleLogout = () => dispatch(logoutUser());

  const initials = user
    ? `${user.firstName?.[0] ?? ""}${user.lastName?.[0] ?? ""}`.toUpperCase() ||
      "U"
    : "U";

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-4 border-b border-border/60 bg-background/80 px-4 backdrop-blur-md lg:px-6">
      {/* Mobile menu button */}
      {isMobile && (
        <Button
          variant="ghost"
          size="icon"
          onClick={onMenuClick}
          className="h-9 w-9 shrink-0"
        >
          <Menu className="h-5 w-5" />
        </Button>
      )}

      {/* Desktop logo spacer - sidebar handles logo */}
      {!isMobile && <div className="hidden lg:block" />}

      {/* Search */}
      <div
        className={cn(
          "flex-1 transition-all",
          searchOpen ? "max-w-md" : "max-w-xs",
        )}
      >
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search transactions, cards..."
            className="h-9 pl-9 text-sm bg-secondary/60 border-transparent focus:border-border focus:bg-background transition-all"
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setSearchOpen(false)}
          />
          {searchOpen && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onMouseDown={() => setSearchOpen(false)}
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9"
          onClick={() => navigate("/notifications")}
        >
          <Bell className="h-4.5 w-4.5" />
          {(unreadNotifications ?? 0) > 0 && (
            <Badge
              variant="destructive"
              className="absolute -right-0.5 -top-0.5 h-4 w-4 rounded-full p-0 text-[9px] font-bold flex items-center justify-center"
            >
              {unreadNotifications}
            </Badge>
          )}
        </Button>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2.5 rounded-xl px-2 py-1.5 hover:bg-secondary transition-colors outline-none">
              <Avatar className="h-7 w-7 ring-2 ring-primary/20">
                <AvatarImage src={user?.profilePicture} />
                <AvatarFallback className="bg-gradient-brand text-white text-xs font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              {!isMobile && (
                <div className="text-left">
                  <p className="text-[13px] font-medium leading-none">
                    {user?.firstName ?? "User"}
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-none">
                    {user?.email ?? ""}
                  </p>
                </div>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel>
              <p className="font-medium">
                {user?.firstName} {user?.lastName}
              </p>
              <p className="text-xs font-normal text-muted-foreground truncate">
                {user?.email}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => navigate("/profile")}
              className="gap-2"
            >
              <User className="h-4 w-4" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => navigate("/settings")}
              className="gap-2"
            >
              <Monitor className="h-4 w-4" /> Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="gap-2 text-destructive focus:text-destructive"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default Header;
