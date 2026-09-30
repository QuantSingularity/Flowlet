import {
  Activity,
  BarChart3,
  CreditCard,
  DollarSign,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const monthlyData = [
  { month: "Aug", income: 3800, expenses: 2400 },
  { month: "Sep", income: 4200, expenses: 2800 },
  { month: "Oct", income: 3900, expenses: 3100 },
  { month: "Nov", income: 4800, expenses: 2600 },
  { month: "Dec", income: 5200, expenses: 3200 },
  { month: "Jan", income: 4200, expenses: 2850 },
];

const spendingData = [
  { category: "Housing", amount: 1200, color: "#6366f1" },
  { category: "Food", amount: 480, color: "#f59e0b" },
  { category: "Transport", amount: 320, color: "#10b981" },
  { category: "Shopping", amount: 280, color: "#ec4899" },
  { category: "Utilities", amount: 220, color: "#3b82f6" },
  { category: "Other", amount: 350, color: "#8b5cf6" },
];

const weeklyData = [
  { day: "Mon", amount: 120 },
  { day: "Tue", amount: 45 },
  { day: "Wed", amount: 280 },
  { day: "Thu", amount: 95 },
  { day: "Fri", amount: 340 },
  { day: "Sat", amount: 210 },
  { day: "Sun", amount: 80 },
];

const stats = [
  {
    title: "Total Transactions",
    value: "1,234",
    change: "+12%",
    up: true,
    icon: Activity,
  },
  {
    title: "Total Volume",
    value: "$45,678",
    change: "+8%",
    up: true,
    icon: DollarSign,
  },
  {
    title: "Active Cards",
    value: "3",
    change: "+1",
    up: true,
    icon: CreditCard,
  },
  {
    title: "Avg Transaction",
    value: "$37.02",
    change: "-2%",
    up: false,
    icon: BarChart3,
  },
];

export default function AnalyticsScreen() {
  const totalSpending = spendingData.reduce((a, b) => a + b.amount, 0);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Track your financial performance and insights
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 stagger-children">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="card-hover">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground font-medium">
                      {stat.title}
                    </p>
                    <p className="text-2xl font-bold tabular-nums">
                      {stat.value}
                    </p>
                    <div className="flex items-center gap-1">
                      {stat.up ? (
                        <TrendingUp className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-red-500" />
                      )}
                      <span
                        className={`text-xs font-medium ${stat.up ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}
                      >
                        {stat.change} vs last month
                      </span>
                    </div>
                  </div>
                  <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="h-9">
          <TabsTrigger value="overview" className="text-xs">
            Overview
          </TabsTrigger>
          <TabsTrigger value="spending" className="text-xs">
            Spending
          </TabsTrigger>
          <TabsTrigger value="weekly" className="text-xs">
            Weekly
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base">Income vs Expenses</CardTitle>
              <CardDescription className="text-xs">
                6-month comparison
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart
                  data={monthlyData}
                  margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="#6366f1"
                        stopOpacity={0.15}
                      />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient
                      id="expenseGrad"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor="#f59e0b"
                        stopOpacity={0.15}
                      />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="hsl(var(--border))"
                  />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => `$${v / 1000}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(val: number) => [
                      `$${val.toLocaleString()}`,
                      "",
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="income"
                    stroke="#6366f1"
                    strokeWidth={2}
                    fill="url(#incomeGrad)"
                    name="Income"
                  />
                  <Area
                    type="monotone"
                    dataKey="expenses"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    fill="url(#expenseGrad)"
                    name="Expenses"
                  />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex items-center justify-center gap-6 mt-3">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-3 h-3 rounded-full bg-indigo-500" />
                  Income
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  Expenses
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="spending">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-base">
                  Spending by Category
                </CardTitle>
                <CardDescription className="text-xs">
                  This month · ${totalSpending.toLocaleString()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={spendingData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={3}
                      dataKey="amount"
                    >
                      {spendingData.map((entry, index) => (
                        <Cell
                          key={index}
                          fill={entry.color}
                          stroke="transparent"
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(val: number) => [
                        `$${val.toLocaleString()}`,
                        "",
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Category Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {spendingData.map((item) => (
                    <div key={item.category}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-2.5 h-2.5 rounded-sm"
                            style={{ background: item.color }}
                          />
                          <span className="font-medium">{item.category}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground text-xs">
                            {Math.round((item.amount / totalSpending) * 100)}%
                          </span>
                          <span className="font-semibold tabular-nums">
                            ${item.amount}
                          </span>
                        </div>
                      </div>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${(item.amount / totalSpending) * 100}%`,
                            background: item.color,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="weekly">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-base">
                Daily Spending - This Week
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={weeklyData}
                  margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="hsl(var(--border))"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => `$${v}`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(val: number) => [`$${val}`, "Spent"]}
                  />
                  <Bar
                    dataKey="amount"
                    fill="hsl(var(--primary))"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
