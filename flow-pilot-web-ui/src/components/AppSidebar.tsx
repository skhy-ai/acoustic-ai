
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
import {
  Workflow,
  Settings,
  Monitor,
  Database,
  Play,
  Mic,
  Waves,
  Brain,
  Target,
  Filter,
  Gauge,
  ShieldCheck,
  LucideIcon,
} from "lucide-react";

/**
 * AppSidebar.tsx
 * ===============
 * Application sidebar with conditional rendering based on install mode.
 *
 * DESIGN NOTE:
 *   In "edge" mode (field/embedded devices), training, augmentation,
 *   data prep, and manual filtering tabs are hidden. Only inference,
 *   DOA/Doppler, calibration, config, and admin remain.
 *
 *   The mode is read from the VITE_INSTALL_MODE environment variable
 *   (set at build time). Default is "development" (all tabs visible).
 */

/* ── Install mode ── */
type InstallMode = 'development' | 'edge';
const INSTALL_MODE: InstallMode =
  ((import.meta as any).env?.VITE_INSTALL_MODE as InstallMode) || 'development';

interface AppSidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

interface NavItem {
  title: string;
  id: string;
  icon: LucideIcon;
  description: string;
  /** If specified, item only shows in these modes */
  modes?: InstallMode[];
}

/* ── Main Navigation Items ── */
const mainNavItems: NavItem[] = [
  {
    title: "Experiment Builder",
    id: "builder",
    icon: Workflow,
    description: "Design workflow pipeline",
  },
  {
    title: "Parameters",
    id: "parameters",
    icon: Settings,
    description: "Configure module settings",
  },
  {
    title: "Live Monitor",
    id: "monitor",
    icon: Monitor,
    description: "Real-time logs & progress",
  },
  {
    title: "Data Viewer",
    id: "data",
    icon: Database,
    description: "Results & visualizations",
  },
  {
    title: "Execution",
    id: "execution",
    icon: Play,
    description: "Run experiments",
  },
  {
    title: "Doppler / Frequency",
    id: "doppler",
    icon: Gauge,
    description: "Doppler & hybrid analysis",
  },
  {
    title: "Manual Filter",
    id: "manual-filter",
    icon: Filter,
    description: "Spectrogram keep/delete",
    modes: ['development'],      // hidden in edge mode
  },
  {
    title: "Admin Panel",
    id: "admin",
    icon: ShieldCheck,
    description: "Backend service control",
  },
];

/* ── AI Module Items ── */
interface ModuleItem {
  title: string;
  icon: LucideIcon;
  description: string;
  modes?: InstallMode[];
}

const moduleItems: ModuleItem[] = [
  {
    title: "M1: Data Acquisition",
    icon: Mic,
    description: "Sensors, streaming, beamforming",
  },
  {
    title: "M2: Preprocessing",
    icon: Waves,
    description: "Chunking, click detection",
    modes: ['development'],
  },
  {
    title: "M3: Augmentation",
    icon: Settings,
    description: "Pitch shift, noise injection",
    modes: ['development'],
  },
  {
    title: "M4: ML Processing",
    icon: Brain,
    description: "Feature extraction, training",
  },
  {
    title: "M5: Applications",
    icon: Target,
    description: "Classification, scene analysis",
  },
];

/**
 * Filter items based on the current install mode.
 * Items without a `modes` array are always visible.
 */
const filterByMode = <T extends { modes?: InstallMode[] }>(items: T[]): T[] =>
  items.filter((item) => !item.modes || item.modes.includes(INSTALL_MODE));

export function AppSidebar({ activeView, onViewChange }: AppSidebarProps) {
  const visibleNav = filterByMode(mainNavItems);
  const visibleModules = filterByMode(moduleItems);

  return (
    <Sidebar className="border-r border-gray-200">
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-2">
          <Waves className="h-8 w-8 text-blue-600" />
          <div>
            <h2 className="text-lg font-semibold">Skhy Acoustic AI</h2>
            <p className="text-sm text-gray-500">
              {INSTALL_MODE === 'edge' ? 'Edge Device' : 'Experiment Platform'}
            </p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {visibleNav.map((item) => (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton
                    isActive={activeView === item.id}
                    onClick={() => onViewChange(item.id)}
                    className="w-full justify-start"
                  >
                    <item.icon className="h-4 w-4" />
                    <div className="flex flex-col items-start">
                      <span className="font-medium">{item.title}</span>
                      <span className="text-xs text-gray-500">{item.description}</span>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>AI Modules</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {visibleModules.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton className="w-full justify-start">
                    <item.icon className="h-4 w-4" />
                    <div className="flex flex-col items-start">
                      <span className="font-medium text-sm">{item.title}</span>
                      <span className="text-xs text-gray-500">{item.description}</span>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4">
        <div className="text-xs text-gray-500">
          <p>Powered by Skhy</p>
          <p className="mt-1">
            Mode: {INSTALL_MODE === 'edge' ? '🔳 Edge' : '🛠️ Dev'} · Status: Ready
          </p>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
