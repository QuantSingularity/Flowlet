import {
  Camera,
  CheckCircle,
  Mail,
  Phone,
  Shield,
  User,
  XCircle,
} from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";

const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  const displayName =
    user?.fullName ||
    `${user?.firstName ?? ""} ${user?.lastName ?? ""}`.trim() ||
    "User";
  const initials =
    [user?.firstName?.[0], user?.lastName?.[0]]
      .filter(Boolean)
      .join("")
      .toUpperCase() || "U";

  const [formData, setFormData] = useState({
    firstName: user?.firstName ?? "",
    lastName: user?.lastName ?? "",
    email: user?.email ?? "",
    phoneNumber: user?.phoneNumber ?? "",
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((r) => setTimeout(r, 800));
    setIsSaving(false);
    toast.success("Profile updated successfully");
  };

  const kycBadgeVariant: "success" | "warning" | "destructive" | "secondary" =
    user?.kycStatus === "completed"
      ? "success"
      : user?.kycStatus === "in_progress"
        ? "warning"
        : user?.kycStatus === "rejected"
          ? "destructive"
          : "secondary";

  const kycLabel =
    user?.kycStatus === "completed"
      ? "Verified"
      : user?.kycStatus === "in_progress"
        ? "In Progress"
        : user?.kycStatus === "rejected"
          ? "Rejected"
          : "Not Started";

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage your personal information and account details
        </p>
      </div>

      {/* Avatar & Identity */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="relative group">
              <Avatar className="h-24 w-24 ring-4 ring-border">
                <AvatarImage src={user?.profilePicture} alt={displayName} />
                <AvatarFallback className="text-2xl font-bold bg-primary text-primary-foreground">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <button
                className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => toast.info("Photo upload coming soon")}
                aria-label="Change profile photo"
              >
                <Camera className="h-6 w-6 text-white" />
              </button>
            </div>

            <div className="flex-1 text-center sm:text-left space-y-2">
              <h2 className="text-xl font-semibold">{displayName}</h2>
              <p className="text-muted-foreground text-sm">{user?.email}</p>
              <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
                <Badge variant={kycBadgeVariant}>
                  <Shield className="h-3 w-3 mr-1" />
                  KYC {kycLabel}
                </Badge>
                <Badge
                  variant={user?.isEmailVerified ? "success" : "secondary"}
                >
                  <Mail className="h-3 w-3 mr-1" />
                  {user?.isEmailVerified
                    ? "Email Verified"
                    : "Email Unverified"}
                </Badge>
                {user?.mfaEnabled && (
                  <Badge variant="success">
                    <Shield className="h-3 w-3 mr-1" />
                    2FA Enabled
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Personal Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <User className="h-4 w-4" />
            Personal Information
          </CardTitle>
          <CardDescription>Update your personal details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="firstName">First name</Label>
              <Input
                id="firstName"
                value={formData.firstName}
                onChange={(e) =>
                  setFormData((p) => ({ ...p, firstName: e.target.value }))
                }
                placeholder="First name"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="lastName">Last name</Label>
              <Input
                id="lastName"
                value={formData.lastName}
                onChange={(e) =>
                  setFormData((p) => ({ ...p, lastName: e.target.value }))
                }
                placeholder="Last name"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="email">Email address</Label>
            <div className="relative">
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData((p) => ({ ...p, email: e.target.value }))
                }
                placeholder="you@example.com"
                className="pr-24"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {user?.isEmailVerified ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Verified
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <XCircle className="h-3.5 w-3.5" />
                    Unverified
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="phone">Phone number</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="phone"
                type="tel"
                value={formData.phoneNumber}
                onChange={(e) =>
                  setFormData((p) => ({ ...p, phoneNumber: e.target.value }))
                }
                placeholder="+1 (555) 000-0000"
                className="pl-9"
              />
            </div>
          </div>

          <Separator />

          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account Information</CardTitle>
          <CardDescription>Read-only account details</CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="space-y-3 text-sm">
            {[
              { label: "Account ID", value: user?.id ?? "-" },
              { label: "Role", value: user?.role ?? "-" },
              {
                label: "Member since",
                value: user?.createdAt
                  ? new Date(user.createdAt).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })
                  : "-",
              },
              {
                label: "Last updated",
                value: user?.updatedAt
                  ? new Date(user.updatedAt).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })
                  : "-",
              },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between gap-4">
                <dt className="text-muted-foreground shrink-0">{label}</dt>
                <dd className="font-medium text-right truncate">{value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProfilePage;
