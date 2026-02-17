import { useMemo } from 'react';
import { IAccessMapping } from '../types';

/**
 * Props for the useAccessControl hook.
 */
interface IAccessControlInput {
    accessMappings: IAccessMapping[];
    userSsoGroups: string[];
    isAdmin: boolean;
}

/**
 * Result of the useAccessControl hook.
 */
export interface IAccessControl {
    /** Whether the user can edit properties of the given component/extension ID. */
    canEdit(extensionId: string): boolean;
    /** Whether the given extension ID is a connection extension (admin-only). */
    isConnectionExtension(extensionId: string, connectionIds: Set<string>): boolean;
    /** Returns the list of process names authorized to access a given extension. */
    getAuthorizedProcesses(extensionId: string): string[];
}

/**
 * Hook for permission checking per extension component.
 *
 * Rules:
 * - Admins (isAdmin=true or ABC_BOOMI_FLOW_ADMIN in groups) can edit everything.
 * - Connection extensions (isConnectionExtension=true) require admin.
 * - Non-admin users with ABC_BOOMI_FLOW_CONTRIBUTOR can edit non-connection extensions.
 * - Extensions on adminOnly processes are read-only for non-admins.
 */
export function useAccessControl({
    accessMappings,
    userSsoGroups,
    isAdmin,
}: IAccessControlInput): IAccessControl {
    const effectiveIsAdmin = useMemo(() => {
        return isAdmin || userSsoGroups.includes('ABC_BOOMI_FLOW_ADMIN');
    }, [isAdmin, userSsoGroups]);

    // Build a map of extensionId -> list of process mappings that include it
    const extensionToProcesses = useMemo<Map<string, IAccessMapping[]>>(() => {
        const map = new Map<string, IAccessMapping[]>();
        for (const mapping of accessMappings) {
            for (const extId of mapping.extensionIds) {
                const existing = map.get(extId) ?? [];
                existing.push(mapping);
                map.set(extId, existing);
            }
        }
        return map;
    }, [accessMappings]);

    const canEdit = useMemo(() => {
        return (extensionId: string): boolean => {
            // Admins can always edit
            if (effectiveIsAdmin) return true;

            // Non-admins cannot edit extensions used by adminOnly processes
            const processes = extensionToProcesses.get(extensionId) ?? [];
            const hasAdminOnlyProcess = processes.some((p) => p.adminOnly);
            if (hasAdminOnlyProcess) return false;

            // Contributors can edit if they have access
            return userSsoGroups.includes('ABC_BOOMI_FLOW_CONTRIBUTOR');
        };
    }, [effectiveIsAdmin, extensionToProcesses, userSsoGroups]);

    const isConnectionExtension = useMemo(() => {
        return (extensionId: string, connectionIds: Set<string>): boolean => {
            return connectionIds.has(extensionId);
        };
    }, []);

    const getAuthorizedProcesses = useMemo(() => {
        return (extensionId: string): string[] => {
            const processes = extensionToProcesses.get(extensionId) ?? [];
            return processes.map((p) => p.processName);
        };
    }, [extensionToProcesses]);

    return {
        canEdit,
        isConnectionExtension,
        getAuthorizedProcesses,
    };
}
