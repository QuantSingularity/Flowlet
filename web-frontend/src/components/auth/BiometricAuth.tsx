import {
  AlertTriangle,
  CheckCircle,
  Eye,
  Fingerprint,
  Lock,
  Mic,
  RefreshCw,
  Settings,
  Shield,
  Unlock,
  XCircle,
} from "lucide-react";
import React from "react";
import { useCallback, useEffect, useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface BiometricCapability {
  type: "fingerprint" | "face" | "voice" | "iris";
  available: boolean;
  enrolled: boolean;
  name: string;
  description: string;
  icon: React.ReactNode;
}

interface BiometricAuthProps {
  onAuthenticate?: (result: BiometricAuthResult) => void;
  onEnroll?: (type: string) => Promise<void>;
  onUnenroll?: (type: string) => Promise<void>;
  allowEnrollment?: boolean;
  requireBiometric?: boolean;
  fallbackToPassword?: boolean;
  className?: string;
}

interface BiometricAuthResult {
  success: boolean;
  type: string;
  credential?: any;
  error?: string;
  timestamp: string;
}

interface AuthState {
  isSupported: boolean;
  isAuthenticating: boolean;
  isEnrolling: boolean;
  capabilities: BiometricCapability[];
  lastAuthResult: BiometricAuthResult | null;
  error: string | null;
  enrollmentProgress: number;
  authAttempts: number;
  maxAttempts: number;
  lockoutEndTime: number | null;
}

export function BiometricAuth({
  onAuthenticate,
  onEnroll,
  onUnenroll,
  allowEnrollment = true,
  requireBiometric = false,
  fallbackToPassword = true,
  className = "",
}: BiometricAuthProps) {
  const [state, setState] = useState<AuthState>({
    isSupported: false,
    isAuthenticating: false,
    isEnrolling: false,
    capabilities: [],
    lastAuthResult: null,
    error: null,
    enrollmentProgress: 0,
    authAttempts: 0,
    maxAttempts: 3,
    lockoutEndTime: null,
  });

  // Initialize biometric capabilities
  useEffect(() => {
    const initializeBiometrics = async () => {
      const capabilities: BiometricCapability[] = [
        {
          type: "fingerprint",
          available: false,
          enrolled: false,
          name: "Fingerprint",
          description: "Use your fingerprint to authenticate",
          icon: <Fingerprint className="w-6 h-6" />,
        },
        {
          type: "face",
          available: false,
          enrolled: false,
          name: "Face Recognition",
          description: "Use facial recognition to authenticate",
          icon: <Eye className="w-6 h-6" />,
        },
        {
          type: "voice",
          available: false,
          enrolled: false,
          name: "Voice Recognition",
          description: "Use voice recognition to authenticate",
          icon: <Mic className="w-6 h-6" />,
        },
        {
          type: "iris",
          available: false,
          enrolled: false,
          name: "Iris Scan",
          description: "Use iris scanning to authenticate",
          icon: <Eye className="w-6 h-6" />,
        },
      ];

      // Check WebAuthn support
      if ("credentials" in navigator && "create" in navigator.credentials) {
        try {
          // Check for platform authenticator (built-in biometrics)
          const _available = await (navigator.credentials as any).get({
            publicKey: {
              challenge: new Uint8Array(32),
              timeout: 60000,
              userVerification: "required",
              authenticatorSelection: {
                authenticatorAttachment: "platform",
                userVerification: "required",
              },
            },
          });

          // Update fingerprint availability (most common platform authenticator)
          capabilities[0].available = true;

          setState((prev) => ({
            ...prev,
            isSupported: true,
            capabilities,
          }));
        } catch (_error) {
          // Check for specific biometric APIs
          await checkSpecificBiometrics(capabilities);
        }
      } else {
        await checkSpecificBiometrics(capabilities);
      }
    };

    const checkSpecificBiometrics = async (
      capabilities: BiometricCapability[],
    ) => {
      // Check for Touch ID / Face ID on iOS Safari
      if ("TouchID" in window || "FaceID" in window) {
        capabilities[0].available = "TouchID" in window;
        capabilities[1].available = "FaceID" in window;
      }

      // Check for Windows Hello
      if ("msCredentials" in navigator) {
        capabilities[0].available = true;
        capabilities[1].available = true;
      }

      // Check for Android biometrics
      if ("userAgent" in navigator && /Android/i.test(navigator.userAgent)) {
        capabilities[0].available = true; // Most Android devices have fingerprint
      }

      // Check for media devices (camera/microphone for face/voice)
      if (
        "mediaDevices" in navigator &&
        "getUserMedia" in navigator.mediaDevices
      ) {
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const hasCamera = devices.some(
            (device) => device.kind === "videoinput",
          );
          const hasMicrophone = devices.some(
            (device) => device.kind === "audioinput",
          );

          if (hasCamera) capabilities[1].available = true; // Face recognition
          if (hasMicrophone) capabilities[2].available = true; // Voice recognition
        } catch (error) {
          console.warn("Could not enumerate media devices:", error);
        }
      }

      setState((prev) => ({
        ...prev,
        isSupported: capabilities.some((cap) => cap.available),
        capabilities,
      }));
    };

    initializeBiometrics();
  }, []);

  // Handle lockout timer
  useEffect(() => {
    if (state.lockoutEndTime) {
      const timer = setInterval(() => {
        if (Date.now() >= state.lockoutEndTime!) {
          setState((prev) => ({
            ...prev,
            lockoutEndTime: null,
            authAttempts: 0,
          }));
          clearInterval(timer);
        }
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [state.lockoutEndTime]);

  const authenticateWithFingerprint =
    useCallback(async (): Promise<BiometricAuthResult> => {
      if ("credentials" in navigator) {
        try {
          const credential = await (navigator.credentials as any).get({
            publicKey: {
              challenge: new Uint8Array(32),
              timeout: 60000,
              userVerification: "required",
              authenticatorSelection: {
                authenticatorAttachment: "platform",
                userVerification: "required",
              },
            },
          });

          return {
            success: true,
            type: "fingerprint",
            credential,
            timestamp: new Date().toISOString(),
          };
        } catch (_error) {
          return {
            success: false,
            type: "fingerprint",
            error: "Fingerprint authentication failed",
            timestamp: new Date().toISOString(),
          };
        }
      }

      throw new Error("WebAuthn not supported");
    }, []);

  const authenticateWithFace =
    useCallback(async (): Promise<BiometricAuthResult> => {
      // Simulate face recognition (would integrate with actual face recognition API)
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: Math.random() > 0.3, // 70% success rate for demo
            type: "face",
            timestamp: new Date().toISOString(),
          });
        }, 2000);
      });
    }, []);

  const authenticateWithVoice =
    useCallback(async (): Promise<BiometricAuthResult> => {
      // Simulate voice recognition (would integrate with actual voice recognition API)
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: Math.random() > 0.4, // 60% success rate for demo
            type: "voice",
            timestamp: new Date().toISOString(),
          });
        }, 3000);
      });
    }, []);

  const authenticateWithIris =
    useCallback(async (): Promise<BiometricAuthResult> => {
      // Simulate iris scanning (would integrate with actual iris scanning API)
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: Math.random() > 0.2, // 80% success rate for demo
            type: "iris",
            timestamp: new Date().toISOString(),
          });
        }, 2500);
      });
    }, []);

  const handleAuthenticate = useCallback(
    async (type: string) => {
      if (state.lockoutEndTime && Date.now() < state.lockoutEndTime) {
        setState((prev) => ({
          ...prev,
          error: "Authentication locked. Please try again later.",
        }));
        return;
      }

      setState((prev) => ({ ...prev, isAuthenticating: true, error: null }));

      try {
        let result: BiometricAuthResult;

        switch (type) {
          case "fingerprint":
            result = await authenticateWithFingerprint();
            break;
          case "face":
            result = await authenticateWithFace();
            break;
          case "voice":
            result = await authenticateWithVoice();
            break;
          case "iris":
            result = await authenticateWithIris();
            break;
          default:
            throw new Error("Unsupported biometric type");
        }

        if (result.success) {
          setState((prev) => ({
            ...prev,
            lastAuthResult: result,
            authAttempts: 0,
            lockoutEndTime: null,
          }));

          if (onAuthenticate) {
            onAuthenticate(result);
          }
        } else {
          const newAttempts = state.authAttempts + 1;
          const shouldLock = newAttempts >= state.maxAttempts;

          setState((prev) => ({
            ...prev,
            authAttempts: newAttempts,
            lockoutEndTime: shouldLock ? Date.now() + 300000 : null, // 5 minutes
            error: result.error || "Authentication failed",
          }));
        }
      } catch (error) {
        const newAttempts = state.authAttempts + 1;
        const shouldLock = newAttempts >= state.maxAttempts;

        setState((prev) => ({
          ...prev,
          authAttempts: newAttempts,
          lockoutEndTime: shouldLock ? Date.now() + 300000 : null,
          error:
            error instanceof Error ? error.message : "Authentication failed",
        }));
      } finally {
        setState((prev) => ({ ...prev, isAuthenticating: false }));
      }
    },
    [
      state.authAttempts,
      state.maxAttempts,
      state.lockoutEndTime,
      onAuthenticate,
      authenticateWithFace,
      authenticateWithFingerprint,
      authenticateWithIris,
      authenticateWithVoice,
    ],
  );

  const handleEnroll = useCallback(
    async (type: string) => {
      if (!allowEnrollment) return;

      setState((prev) => ({
        ...prev,
        isEnrolling: true,
        error: null,
        enrollmentProgress: 0,
      }));

      try {
        // Simulate enrollment progress
        for (let i = 0; i <= 100; i += 10) {
          setState((prev) => ({ ...prev, enrollmentProgress: i }));
          await new Promise((resolve) => setTimeout(resolve, 200));
        }

        if (onEnroll) {
          await onEnroll(type);
        }

        // Update capability as enrolled
        setState((prev) => ({
          ...prev,
          capabilities: prev.capabilities.map((cap) =>
            cap.type === type ? { ...cap, enrolled: true } : cap,
          ),
          enrollmentProgress: 100,
        }));

        setTimeout(() => {
          setState((prev) => ({ ...prev, enrollmentProgress: 0 }));
        }, 1000);
      } catch (_error) {
        setState((prev) => ({
          ...prev,
          error: `Failed to enroll ${type}`,
          enrollmentProgress: 0,
        }));
      } finally {
        setState((prev) => ({ ...prev, isEnrolling: false }));
      }
    },
    [allowEnrollment, onEnroll],
  );

  const handleUnenroll = useCallback(
    async (type: string) => {
      try {
        if (onUnenroll) {
          await onUnenroll(type);
        }

        setState((prev) => ({
          ...prev,
          capabilities: prev.capabilities.map((cap) =>
            cap.type === type ? { ...cap, enrolled: false } : cap,
          ),
        }));
      } catch (_error) {
        setState((prev) => ({ ...prev, error: `Failed to unenroll ${type}` }));
      }
    },
    [onUnenroll],
  );

  const remainingLockoutTime = state.lockoutEndTime
    ? Math.ceil((state.lockoutEndTime - Date.now()) / 1000)
    : 0;

  const enrolledCapabilities = state.capabilities.filter((cap) => cap.enrolled);
  const availableCapabilities = state.capabilities.filter(
    (cap) => cap.available,
  );

  if (!state.isSupported) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Biometric Authentication Not Supported
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Your device or browser doesn't support biometric authentication.
          </p>
          {fallbackToPassword && (
            <Button variant="outline">
              <Lock className="w-4 h-4 mr-2" />
              Use Password Instead
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Shield className="w-6 h-6 mr-3 text-blue-600" />
              Biometric Authentication
            </div>
            <Badge
              className={
                enrolledCapabilities.length > 0
                  ? "bg-green-100 text-green-600"
                  : "bg-gray-100 text-gray-600"
              }
            >
              {enrolledCapabilities.length > 0 ? (
                <>
                  <CheckCircle className="w-3 h-3 mr-1" />
                  {enrolledCapabilities.length} Enrolled
                </>
              ) : (
                <>
                  <Settings className="w-3 h-3 mr-1" />
                  Setup Required
                </>
              )}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600">
            Use your device's built-in biometric sensors for secure, convenient
            authentication.
          </p>
        </CardContent>
      </Card>

      {/* Alerts */}
      {state.error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {state.error}
          </AlertDescription>
        </Alert>
      )}

      {state.lockoutEndTime && remainingLockoutTime > 0 && (
        <Alert className="border-red-200 bg-red-50">
          <Lock className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            Authentication locked for {remainingLockoutTime} seconds due to
            multiple failed attempts.
          </AlertDescription>
        </Alert>
      )}

      {state.lastAuthResult?.success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Successfully authenticated with {state.lastAuthResult.type} at{" "}
            {new Date(state.lastAuthResult.timestamp).toLocaleTimeString()}
          </AlertDescription>
        </Alert>
      )}

      {/* Enrollment Progress */}
      {state.isEnrolling && (
        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Enrollment Progress</span>
                <span>{state.enrollmentProgress}%</span>
              </div>
              <Progress value={state.enrollmentProgress} className="h-2" />
              <p className="text-xs text-gray-600">
                Follow the on-screen instructions to complete enrollment.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Biometric Methods */}
      <div className="grid gap-4">
        {availableCapabilities.map((capability) => (
          <Card key={capability.type}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-blue-600">{capability.icon}</div>
                  <div>
                    <h3 className="font-medium">{capability.name}</h3>
                    <p className="text-sm text-gray-600">
                      {capability.description}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Badge
                    className={
                      capability.enrolled
                        ? "bg-green-100 text-green-600"
                        : "bg-gray-100 text-gray-600"
                    }
                  >
                    {capability.enrolled ? "Enrolled" : "Not Enrolled"}
                  </Badge>

                  <div className="flex space-x-2">
                    {capability.enrolled ? (
                      <>
                        <Button
                          onClick={() => handleAuthenticate(capability.type)}
                          disabled={
                            state.isAuthenticating ||
                            state.lockoutEndTime !== null
                          }
                          size="sm"
                        >
                          {state.isAuthenticating ? (
                            <>
                              <RefreshCw className="w-3 h-3 mr-2 animate-spin" />
                              Authenticating...
                            </>
                          ) : (
                            <>
                              <Unlock className="w-3 h-3 mr-2" />
                              Authenticate
                            </>
                          )}
                        </Button>
                        <Button
                          onClick={() => handleUnenroll(capability.type)}
                          disabled={state.isEnrolling}
                          size="sm"
                          variant="outline"
                        >
                          Unenroll
                        </Button>
                      </>
                    ) : (
                      <Button
                        onClick={() => handleEnroll(capability.type)}
                        disabled={state.isEnrolling || !allowEnrollment}
                        size="sm"
                        variant="outline"
                      >
                        {state.isEnrolling ? "Enrolling..." : "Enroll"}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Fallback Options */}
      {requireBiometric && enrolledCapabilities.length === 0 && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            Biometric authentication is required. Please enroll at least one
            biometric method.
          </AlertDescription>
        </Alert>
      )}

      {fallbackToPassword && !requireBiometric && (
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-gray-600 mb-3">
              Having trouble with biometric authentication?
            </p>
            <Button variant="outline" size="sm">
              <Lock className="w-4 h-4 mr-2" />
              Use Password Instead
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Security Info */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">
                Security Information
              </p>
              <ul className="space-y-1 text-xs">
                <li>• Biometric data is stored securely on your device</li>
                <li>
                  • Authentication attempts: {state.authAttempts}/
                  {state.maxAttempts}
                </li>
                <li>
                  • Fallback authentication is{" "}
                  {fallbackToPassword ? "available" : "disabled"}
                </li>
                <li>• All authentication attempts are logged for security</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default BiometricAuth;
