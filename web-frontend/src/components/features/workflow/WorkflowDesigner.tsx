import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  BarChart3,
  Calculator,
  CheckCircle,
  Clock,
  CreditCard,
  Database,
  DollarSign,
  FileText,
  Filter,
  GitBranch,
  Globe,
  Mail,
  MessageSquare,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Save,
  Shield,
  Trash2,
  Users,
  Zap,
} from "lucide-react";
import React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

import "./workflow.css";

// Types for workflow nodes and connections
export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    config?: Record<string, any>;
    status?: "idle" | "running" | "completed" | "error";
  };
}

export interface WorkflowConnection {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  connections: WorkflowConnection[];
  status: "draft" | "active" | "paused" | "archived";
  createdAt: Date;
  updatedAt: Date;
  version: number;
}

// Node types for FinTech workflows
const NODE_TYPES = {
  trigger: {
    category: "Triggers",
    items: [
      {
        type: "payment_received",
        label: "Payment Received",
        icon: DollarSign,
        color: "bg-green-500",
      },
      {
        type: "transaction_created",
        label: "Transaction Created",
        icon: CreditCard,
        color: "bg-blue-500",
      },
      {
        type: "user_registered",
        label: "User Registered",
        icon: Users,
        color: "bg-purple-500",
      },
      {
        type: "schedule",
        label: "Schedule",
        icon: Clock,
        color: "bg-orange-500",
      },
      {
        type: "webhook",
        label: "Webhook",
        icon: Globe,
        color: "bg-indigo-500",
      },
    ],
  },
  action: {
    category: "Actions",
    items: [
      {
        type: "send_payment",
        label: "Send Payment",
        icon: DollarSign,
        color: "bg-green-600",
      },
      {
        type: "create_card",
        label: "Create Card",
        icon: CreditCard,
        color: "bg-blue-600",
      },
      {
        type: "send_notification",
        label: "Send Notification",
        icon: MessageSquare,
        color: "bg-yellow-600",
      },
      {
        type: "send_email",
        label: "Send Email",
        icon: Mail,
        color: "bg-red-600",
      },
      {
        type: "update_database",
        label: "Update Database",
        icon: Database,
        color: "bg-gray-600",
      },
      {
        type: "generate_report",
        label: "Generate Report",
        icon: FileText,
        color: "bg-teal-600",
      },
    ],
  },
  condition: {
    category: "Logic",
    items: [
      {
        type: "if_condition",
        label: "If Condition",
        icon: GitBranch,
        color: "bg-amber-500",
      },
      { type: "filter", label: "Filter", icon: Filter, color: "bg-cyan-500" },
      {
        type: "calculator",
        label: "Calculator",
        icon: Calculator,
        color: "bg-pink-500",
      },
      { type: "delay", label: "Delay", icon: Clock, color: "bg-slate-500" },
    ],
  },
  security: {
    category: "Security & Compliance",
    items: [
      {
        type: "fraud_check",
        label: "Fraud Check",
        icon: Shield,
        color: "bg-red-500",
      },
      {
        type: "compliance_check",
        label: "Compliance Check",
        icon: CheckCircle,
        color: "bg-emerald-500",
      },
      {
        type: "risk_assessment",
        label: "Risk Assessment",
        icon: AlertTriangle,
        color: "bg-orange-600",
      },
      {
        type: "kyc_verification",
        label: "KYC Verification",
        icon: Users,
        color: "bg-violet-500",
      },
    ],
  },
  analytics: {
    category: "Analytics",
    items: [
      {
        type: "track_event",
        label: "Track Event",
        icon: BarChart3,
        color: "bg-blue-700",
      },
      {
        type: "analytics_report",
        label: "Analytics Report",
        icon: BarChart3,
        color: "bg-green-700",
      },
    ],
  },
};

interface WorkflowDesignerProps {
  workflowId?: string | null;
}

const WorkflowDesigner: React.FC<WorkflowDesignerProps> = ({ workflowId }) => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [currentWorkflow, setCurrentWorkflow] = useState<Workflow | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [draggedNodeType, setDraggedNodeType] = useState<string | null>(null);
  const [_showNodeConfig, _setShowNodeConfig] = useState(false);
  const [canvasOffset, _setCanvasOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const canvasRef = useRef<HTMLDivElement>(null);
  const [_connectionStart, _setConnectionStart] = useState<{
    nodeId: string;
    handle: string;
  } | null>(null);

  // Create new workflow
  const createNewWorkflow = useCallback(() => {
    const newWorkflow: Workflow = {
      id: `workflow_${Date.now()}`,
      name: "New Workflow",
      description: "A new financial workflow",
      nodes: [],
      connections: [],
      status: "draft",
      createdAt: new Date(),
      updatedAt: new Date(),
      version: 1,
    };
    setWorkflows((prev) => [...prev, newWorkflow]);
    setCurrentWorkflow(newWorkflow);
  }, []);

  // Add node to canvas
  const addNode = useCallback(
    (nodeType: string, position: { x: number; y: number }) => {
      if (!currentWorkflow) return;

      const nodeInfo = Object.values(NODE_TYPES)
        .flatMap((category) => category.items)
        .find((item) => item.type === nodeType);

      if (!nodeInfo) return;

      const newNode: WorkflowNode = {
        id: `node_${Date.now()}`,
        type: nodeType,
        position,
        data: {
          label: nodeInfo.label,
          description: `${nodeInfo.label} node`,
          config: {},
          status: "idle",
        },
      };

      const updatedWorkflow = {
        ...currentWorkflow,
        nodes: [...currentWorkflow.nodes, newNode],
        updatedAt: new Date(),
      };

      setCurrentWorkflow(updatedWorkflow);
      setWorkflows((prev) =>
        prev.map((w) => (w.id === currentWorkflow.id ? updatedWorkflow : w)),
      );
    },
    [currentWorkflow],
  );

  // Handle canvas drop
  const handleCanvasDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!draggedNodeType || !canvasRef.current) return;

      const rect = canvasRef.current.getBoundingClientRect();
      const position = {
        x: (e.clientX - rect.left - canvasOffset.x) / zoom,
        y: (e.clientY - rect.top - canvasOffset.y) / zoom,
      };

      addNode(draggedNodeType, position);
      setDraggedNodeType(null);
    },
    [draggedNodeType, canvasOffset, zoom, addNode],
  );

  // Delete node
  const deleteNode = useCallback(
    (nodeId: string) => {
      if (!currentWorkflow) return;

      const updatedWorkflow = {
        ...currentWorkflow,
        nodes: currentWorkflow.nodes.filter((n) => n.id !== nodeId),
        connections: currentWorkflow.connections.filter(
          (c) => c.source !== nodeId && c.target !== nodeId,
        ),
        updatedAt: new Date(),
      };

      setCurrentWorkflow(updatedWorkflow);
      setWorkflows((prev) =>
        prev.map((w) => (w.id === currentWorkflow.id ? updatedWorkflow : w)),
      );
      setSelectedNode(null);
    },
    [currentWorkflow],
  );

  // Update node
  const updateNode = useCallback(
    (nodeId: string, updates: Partial<WorkflowNode>) => {
      if (!currentWorkflow) return;

      const updatedWorkflow = {
        ...currentWorkflow,
        nodes: currentWorkflow.nodes.map((n) =>
          n.id === nodeId ? { ...n, ...updates } : n,
        ),
        updatedAt: new Date(),
      };

      setCurrentWorkflow(updatedWorkflow);
      setWorkflows((prev) =>
        prev.map((w) => (w.id === currentWorkflow.id ? updatedWorkflow : w)),
      );
    },
    [currentWorkflow],
  );

  // Run workflow simulation
  const runWorkflow = useCallback(async () => {
    if (!currentWorkflow || isRunning) return;

    setIsRunning(true);

    // Simulate workflow execution
    for (const node of currentWorkflow.nodes) {
      updateNode(node.id, { data: { ...node.data, status: "running" } });
      await new Promise((resolve) => setTimeout(resolve, 1000));
      updateNode(node.id, { data: { ...node.data, status: "completed" } });
    }

    setIsRunning(false);
  }, [currentWorkflow, isRunning, updateNode]);

  // Initialize with sample workflow
  useEffect(() => {
    if (workflows.length === 0) {
      createNewWorkflow();
    }
  }, [workflows.length, createNewWorkflow]);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b bg-card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Zap className="h-6 w-6 text-primary" />
              Workflow Designer
            </h1>
            {currentWorkflow && (
              <div className="flex items-center gap-2">
                <Input
                  value={currentWorkflow.name}
                  onChange={(e) => {
                    const updatedWorkflow = {
                      ...currentWorkflow,
                      name: e.target.value,
                    };
                    setCurrentWorkflow(updatedWorkflow);
                    setWorkflows((prev) =>
                      prev.map((w) =>
                        w.id === currentWorkflow.id ? updatedWorkflow : w,
                      ),
                    );
                  }}
                  className="w-48"
                />
                <Badge
                  variant={
                    currentWorkflow.status === "active"
                      ? "default"
                      : "secondary"
                  }
                >
                  {currentWorkflow.status}
                </Badge>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={createNewWorkflow}>
              <Plus className="h-4 w-4 mr-2" />
              New
            </Button>
            <Button variant="outline" size="sm">
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
            <Button
              variant={isRunning ? "destructive" : "default"}
              size="sm"
              onClick={runWorkflow}
              disabled={!currentWorkflow || currentWorkflow.nodes.length === 0}
            >
              {isRunning ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Node Palette */}
        <div className="w-80 border-r bg-card">
          <ScrollArea className="h-full">
            <div className="p-4">
              <h3 className="font-semibold mb-4">Node Library</h3>

              {Object.entries(NODE_TYPES).map(([categoryKey, category]) => (
                <div key={categoryKey} className="mb-6">
                  <h4 className="text-sm font-medium text-muted-foreground mb-3">
                    {category.category}
                  </h4>
                  <div className="space-y-2">
                    {category.items.map((nodeType) => {
                      const Icon = nodeType.icon;
                      return (
                        <motion.div
                          key={nodeType.type}
                          className="flex items-center gap-3 p-3 rounded-lg border cursor-grab hover:bg-accent transition-colors"
                          draggable
                          onDragStart={() => setDraggedNodeType(nodeType.type)}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <div
                            className={`p-2 rounded ${nodeType.color} text-white`}
                          >
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="flex-1">
                            <div className="font-medium text-sm">
                              {nodeType.label}
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Canvas */}
        <div className="flex-1 relative overflow-hidden">
          <div
            ref={canvasRef}
            className="w-full h-full bg-grid-pattern relative"
            onDrop={handleCanvasDrop}
            onDragOver={(e) => e.preventDefault()}
            style={{
              backgroundPosition: `${canvasOffset.x}px ${canvasOffset.y}px`,
              backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
            }}
          >
            {/* Canvas Controls */}
            <div className="absolute top-4 right-4 flex gap-2 z-10">
              <Button variant="outline" size="sm" onClick={() => setZoom(1)}>
                <RotateCcw className="h-4 w-4" />
              </Button>
              <div className="flex items-center gap-2 bg-card border rounded-md px-3 py-1">
                <span className="text-sm">Zoom:</span>
                <span className="text-sm font-mono">
                  {Math.round(zoom * 100)}%
                </span>
              </div>
            </div>

            {/* Workflow Nodes */}
            <AnimatePresence>
              {currentWorkflow?.nodes.map((node) => {
                const nodeInfo = Object.values(NODE_TYPES)
                  .flatMap((category) => category.items)
                  .find((item) => item.type === node.type);

                if (!nodeInfo) return null;

                const Icon = nodeInfo.icon;

                return (
                  <motion.div
                    key={node.id}
                    className={`absolute bg-card border-2 rounded-lg p-4 cursor-pointer min-w-[200px] ${
                      selectedNode?.id === node.id
                        ? "border-primary"
                        : "border-border"
                    } ${node.data.status === "running" ? "animate-pulse" : ""}`}
                    style={{
                      left: node.position.x * zoom + canvasOffset.x,
                      top: node.position.y * zoom + canvasOffset.y,
                      transform: `scale(${zoom})`,
                    }}
                    onClick={() => setSelectedNode(node)}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    whileHover={{ scale: zoom * 1.05 }}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className={`p-2 rounded ${nodeInfo.color} text-white`}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{node.data.label}</div>
                        {node.data.description && (
                          <div className="text-xs text-muted-foreground">
                            {node.data.description}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-1">
                        {node.data.status === "completed" && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {node.data.status === "error" && (
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                        )}
                        {node.data.status === "running" && (
                          <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        )}
                      </div>
                    </div>

                    {/* Connection handles */}
                    <div className="absolute -right-2 top-1/2 w-4 h-4 bg-primary rounded-full border-2 border-background cursor-crosshair" />
                    <div className="absolute -left-2 top-1/2 w-4 h-4 bg-secondary rounded-full border-2 border-background cursor-crosshair" />
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* Empty state */}
            {currentWorkflow && currentWorkflow.nodes.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <Zap className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium mb-2">
                    Start Building Your Workflow
                  </h3>
                  <p className="text-sm">
                    Drag nodes from the palette to begin creating your financial
                    workflow
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Properties Panel */}
        <AnimatePresence>
          {selectedNode && (
            <motion.div
              className="w-80 border-l bg-card"
              initial={{ x: 320 }}
              animate={{ x: 0 }}
              exit={{ x: 320 }}
            >
              <div className="p-4 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Node Properties</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteNode(selectedNode.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <ScrollArea className="h-full">
                <div className="p-4 space-y-4">
                  <div>
                    <Label htmlFor="node-label">Label</Label>
                    <Input
                      id="node-label"
                      value={selectedNode.data.label}
                      onChange={(e) =>
                        updateNode(selectedNode.id, {
                          data: { ...selectedNode.data, label: e.target.value },
                        })
                      }
                    />
                  </div>

                  <div>
                    <Label htmlFor="node-description">Description</Label>
                    <Textarea
                      id="node-description"
                      value={selectedNode.data.description || ""}
                      onChange={(e) =>
                        updateNode(selectedNode.id, {
                          data: {
                            ...selectedNode.data,
                            description: e.target.value,
                          },
                        })
                      }
                    />
                  </div>

                  <Separator />

                  {/* Node-specific configuration */}
                  <div>
                    <h4 className="font-medium mb-3">Configuration</h4>
                    <NodeConfiguration
                      node={selectedNode}
                      onUpdate={(config) =>
                        updateNode(selectedNode.id, {
                          data: { ...selectedNode.data, config },
                        })
                      }
                    />
                  </div>
                </div>
              </ScrollArea>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Node Configuration Component
const NodeConfiguration: React.FC<{
  node: WorkflowNode;
  onUpdate: (config: Record<string, any>) => void;
}> = ({ node, onUpdate }) => {
  const config = node.data.config || {};

  const renderConfigForNodeType = () => {
    switch (node.type) {
      case "payment_received":
        return (
          <div className="space-y-3">
            <div>
              <Label>Minimum Amount</Label>
              <Input
                type="number"
                value={config.minAmount || ""}
                onChange={(e) =>
                  onUpdate({ ...config, minAmount: e.target.value })
                }
                placeholder="0.00"
              />
            </div>
            <div>
              <Label>Currency</Label>
              <Select
                value={config.currency || "USD"}
                onValueChange={(value) =>
                  onUpdate({ ...config, currency: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case "send_notification":
        return (
          <div className="space-y-3">
            <div>
              <Label>Message Template</Label>
              <Textarea
                value={config.message || ""}
                onChange={(e) =>
                  onUpdate({ ...config, message: e.target.value })
                }
                placeholder="Enter notification message..."
              />
            </div>
            <div>
              <Label>Priority</Label>
              <Select
                value={config.priority || "normal"}
                onValueChange={(value) =>
                  onUpdate({ ...config, priority: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case "fraud_check":
        return (
          <div className="space-y-3">
            <div>
              <Label>Risk Threshold</Label>
              <Slider
                value={[config.riskThreshold || 50]}
                onValueChange={([value]: number[]) =>
                  onUpdate({ ...config, riskThreshold: value })
                }
                max={100}
                step={1}
                className="mt-2"
              />
              <div className="text-sm text-muted-foreground mt-1">
                Current: {config.riskThreshold || 50}%
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                checked={config.blockSuspicious || false}
                onCheckedChange={(checked: boolean) =>
                  onUpdate({ ...config, blockSuspicious: checked })
                }
              />
              <Label>Block suspicious transactions</Label>
            </div>
          </div>
        );

      case "delay":
        return (
          <div className="space-y-3">
            <div>
              <Label>Delay Duration</Label>
              <Input
                type="number"
                value={config.duration || ""}
                onChange={(e) =>
                  onUpdate({ ...config, duration: e.target.value })
                }
                placeholder="5"
              />
            </div>
            <div>
              <Label>Unit</Label>
              <Select
                value={config.unit || "minutes"}
                onValueChange={(value) => onUpdate({ ...config, unit: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="seconds">Seconds</SelectItem>
                  <SelectItem value="minutes">Minutes</SelectItem>
                  <SelectItem value="hours">Hours</SelectItem>
                  <SelectItem value="days">Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      default:
        return (
          <div className="text-sm text-muted-foreground">
            No specific configuration available for this node type.
          </div>
        );
    }
  };

  return <div>{renderConfigForNodeType()}</div>;
};

export default WorkflowDesigner;
