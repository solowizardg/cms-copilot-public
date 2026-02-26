import { React } from "../../hooks";

export const TargetIcon = ({ color }: { color: string }) => (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="20" cy="20" r="18" stroke={color} strokeWidth="2" />
        <circle cx="20" cy="20" r="12" stroke={color} strokeWidth="2" />
        <circle cx="20" cy="20" r="6" fill={color} />
        <path d="M20 2V6M20 34V38M2 20H6M34 20H38" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
);

export const TreeIcon = ({ color }: { color: string }) => (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 3V7M12 7L8 11M12 7L16 11M8 11V15L6 18M8 11V15L10 18M16 11V15L14 18M16 11V15L18 18" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="7" r="1" fill={color} />
        <circle cx="8" cy="11" r="1" fill={color} />
        <circle cx="16" cy="11" r="1" fill={color} />
    </svg>
);

export const DocIcon = ({ color }: { color: string }) => (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="5" y="3" width="14" height="18" rx="2" stroke={color} strokeWidth="2" />
        <path d="M9 7H15M9 11H15M9 15H12" stroke={color} strokeWidth="2" strokeLinecap="round" />
        <circle cx="18" cy="6" r="4" fill="#fff" stroke={color} strokeWidth="2" />
        <path d="M16.5 6L17.5 7L19.5 5" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const CheckIcon = ({ size = 24, color = "currentColor" }: { size?: number; color?: string }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
);

export const CloseIcon = ({ size = 24, color = "currentColor" }: { size?: number; color?: string }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
);

export const StarIcon = ({ size = 12, color = "currentColor" }: { size?: number; color?: string }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
        <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
    </svg>
);
