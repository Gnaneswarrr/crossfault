import { Flame, Globe, Search, Link2 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { CandidateType } from '../api/types';

export interface CategoryInfo {
  type: CandidateType | string;
  label: string;
  shortLabel: string;
  icon: LucideIcon;
  emoji: string;
  badgeClass: string;
}

export function getCategoryInfo(typeStr: string): CategoryInfo {
  switch (typeStr) {
    case 'ACCESS_RULE_CHANGE':
      return {
        type: 'ACCESS_RULE_CHANGE',
        label: 'FIREWALL / ACCESS RULE CHANGE',
        shortLabel: 'FIREWALL / ACCESS RULE',
        icon: Flame,
        emoji: '🔥',
        badgeClass: 'category-firewall',
      };
    case 'ROUTE_CHANGE':
      return {
        type: 'ROUTE_CHANGE',
        label: 'ROUTE / BGP CHANGE',
        shortLabel: 'ROUTE / BGP',
        icon: Globe,
        emoji: '🌐',
        badgeClass: 'category-route',
      };
    case 'DNS_CHANGE':
      return {
        type: 'DNS_CHANGE',
        label: 'DNS CHANGE',
        shortLabel: 'DNS',
        icon: Search,
        emoji: '🔎',
        badgeClass: 'category-dns',
      };
    case 'LIS_PATH_INTERRUPTION':
    default:
      return {
        type: 'LIS_PATH_INTERRUPTION',
        label: 'NETWORK PATH INTERRUPTION',
        shortLabel: 'PATH INTERRUPTION',
        icon: Link2,
        emoji: '🔗',
        badgeClass: 'category-path',
      };
  }
}
