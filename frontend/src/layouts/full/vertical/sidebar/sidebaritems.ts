export interface ChildItem {
  id?: number | string;
  name: string;
  icon?: LucideIcon;
  items?: ChildItem[];
  item?: unknown;
  url?: string;
  color?: string;
  disabled?: boolean;
  subtitle?: string;
  badge?: boolean;
  badgeType?: string;
  badgeContent?: string;
  isActive?: boolean;
  external?: boolean;
  isPro?: boolean;
}

export interface MenuItem {
  heading?: string;
  name?: string;
  icon?: LucideIcon;
  id?: number;
  to?: string;
  item?: MenuItem[];
  items?: ChildItem[];
  url?: string;
  disabled?: boolean;
  subtitle?: string;
  badgeType?: string;
  badge?: boolean;
  badgeContent?: string;
  isActive?: boolean;
  isPro?: boolean;
}

import { uniqueId } from 'lodash';
import {
  LayoutDashboard,
  Activity,
  Clock,
  Settings,
  LucideIcon,
} from 'lucide-react';

const SidebarContent: MenuItem[] = [
  {
    heading: 'PSA Nexus',
    items: [
      {
        id: uniqueId(),
        name: 'Dashboard',
        icon: LayoutDashboard,
        url: '/',
      },
      {
        id: uniqueId(),
        name: 'Agent Trace',
        icon: Activity,
        url: '/trace',
      },
      {
        id: uniqueId(),
        name: 'History',
        icon: Clock,
        url: '/history',
      },
      {
        id: uniqueId(),
        name: 'Settings',
        icon: Settings,
        url: 'http://localhost:8000/admin',
        external: true,
      },
    ],
  },
];

export default SidebarContent;
