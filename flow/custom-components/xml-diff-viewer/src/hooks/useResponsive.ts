import { useState, useEffect } from 'react';
import { Breakpoint, ViewMode } from '../types';

const DESKTOP_QUERY = '(min-width: 1025px)';
const TABLET_QUERY = '(min-width: 768px) and (max-width: 1024px)';

/**
 * Detects responsive breakpoint and returns the appropriate default view mode.
 *
 * - Desktop (>1024px): split view default, user can toggle
 * - Tablet (768-1024px): unified default, user can toggle to split
 * - Mobile (<768px): unified forced, split toggle hidden
 */
export function useResponsive(): {
    breakpoint: Breakpoint;
    defaultViewMode: ViewMode;
    canToggleSplit: boolean;
} {
    const [breakpoint, setBreakpoint] = useState<Breakpoint>(() => {
        if (typeof window === 'undefined') return 'desktop';
        if (window.matchMedia(DESKTOP_QUERY).matches) return 'desktop';
        if (window.matchMedia(TABLET_QUERY).matches) return 'tablet';
        return 'mobile';
    });

    useEffect(() => {
        if (typeof window === 'undefined') return;

        const desktopMql = window.matchMedia(DESKTOP_QUERY);
        const tabletMql = window.matchMedia(TABLET_QUERY);

        const update = () => {
            if (desktopMql.matches) {
                setBreakpoint('desktop');
            } else if (tabletMql.matches) {
                setBreakpoint('tablet');
            } else {
                setBreakpoint('mobile');
            }
        };

        desktopMql.addEventListener('change', update);
        tabletMql.addEventListener('change', update);

        return () => {
            desktopMql.removeEventListener('change', update);
            tabletMql.removeEventListener('change', update);
        };
    }, []);

    return {
        breakpoint,
        defaultViewMode: breakpoint === 'desktop' ? 'split' : 'unified',
        canToggleSplit: breakpoint !== 'mobile',
    };
}
