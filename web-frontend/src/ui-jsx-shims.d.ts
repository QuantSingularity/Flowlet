// Ambient declarations for the shadcn UI primitives that ship as untyped .jsx.
//
// These components live under src/components/ui/*.jsx and have no type
// declarations, which makes the TypeScript compiler report TS7016 wherever a
// .tsx file imports them. Declaring the modules here resolves those imports
// without enabling allowJs (which infers destructured props as required and
// produces false "property is missing" errors on these primitives).
//
// Follow-up recommendation: migrate these primitives to typed .tsx using
// React.ComponentProps<typeof Primitive> so consumers get precise prop types.

declare module "@/components/ui/accordion";
declare module "@/components/ui/alert-dialog";
declare module "@/components/ui/aspect-ratio";
declare module "@/components/ui/avatar";
declare module "@/components/ui/breadcrumb";
declare module "@/components/ui/calendar";
declare module "@/components/ui/carousel";
declare module "@/components/ui/chart";
declare module "@/components/ui/collapsible";
declare module "@/components/ui/command";
declare module "@/components/ui/context-menu";
declare module "@/components/ui/dialog";
declare module "@/components/ui/drawer";
declare module "@/components/ui/dropdown-menu";
declare module "@/components/ui/form";
declare module "@/components/ui/hover-card";
declare module "@/components/ui/input-otp";
declare module "@/components/ui/menubar";
declare module "@/components/ui/navigation-menu";
declare module "@/components/ui/pagination";
declare module "@/components/ui/popover";
declare module "@/components/ui/radio-group";
declare module "@/components/ui/resizable";
declare module "@/components/ui/scroll-area";
declare module "@/components/ui/separator";
declare module "@/components/ui/sheet";
declare module "@/components/ui/sidebar";
declare module "@/components/ui/skeleton";
declare module "@/components/ui/slider";
declare module "@/components/ui/sonner";
declare module "@/components/ui/switch";
declare module "@/components/ui/table";
declare module "@/components/ui/toggle-group";
declare module "@/components/ui/toggle";
declare module "@/components/ui/tooltip";
