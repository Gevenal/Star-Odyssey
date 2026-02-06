// Temporary type declarations for modules
// These will be removed once node_modules are properly installed

declare module 'clsx' {
  type ClassValue = string | number | boolean | undefined | null | { [key: string]: any } | ClassValue[];
  
  function clsx(...inputs: ClassValue[]): string;
  export default clsx;
}

declare module 'lucide-react' {
  import { FC, SVGProps } from 'react';
  
  export interface IconProps extends SVGProps<SVGSVGElement> {
    size?: string | number;
    strokeWidth?: string | number;
  }
  
  export const Settings: FC<IconProps>;
  export const Save: FC<IconProps>;
  export const LogOut: FC<IconProps>;
  export const AlertTriangle: FC<IconProps>;
  export const X: FC<IconProps>;
  export const Heart: FC<IconProps>;
  export const Brain: FC<IconProps>;
  export const MapPin: FC<IconProps>;
  export const Activity: FC<IconProps>;
  export const Skull: FC<IconProps>;
  export const Users: FC<IconProps>;
  export const Filter: FC<IconProps>;
  export const BookOpen: FC<IconProps>;
  export const User: FC<IconProps>;
  export const Cpu: FC<IconProps>;
  export const AlertCircle: FC<IconProps>;
  export const Wrench: FC<IconProps>;
  export const Stethoscope: FC<IconProps>;
  export const Zap: FC<IconProps>;
  export const Droplet: FC<IconProps>;
  export const Package: FC<IconProps>;
  export const Crosshair: FC<IconProps>;
  export const MessageSquare: FC<IconProps>;
  export const Search: FC<IconProps>;
  export const Play: FC<IconProps>;
  export const Pause: FC<IconProps>;
  export const SkipForward: FC<IconProps>;
}
