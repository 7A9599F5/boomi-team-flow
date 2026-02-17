/**
 * @jest-environment jsdom
 */
import { renderHook } from '@testing-library/react-hooks';
import { useAccessControl } from '../hooks/useAccessControl';
import { IAccessMapping } from '../types';

const sampleMappings: IAccessMapping[] = [
    {
        processId: 'proc-1',
        processName: 'Order Processing',
        extensionIds: ['conn-1', 'op-1', 'pp-1'],
        adminOnly: false,
    },
    {
        processId: 'proc-2',
        processName: 'SAP Integration',
        extensionIds: ['conn-2', 'pp-1'],
        adminOnly: true,
    },
];

const connectionIds = new Set(['conn-1', 'conn-2']);

describe('useAccessControl', () => {
    describe('canEdit', () => {
        it('returns true for admin users on any extension', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: ['ABC_BOOMI_FLOW_ADMIN'],
                    isAdmin: true,
                }),
            );
            expect(result.current.canEdit('conn-1')).toBe(true);
            expect(result.current.canEdit('conn-2')).toBe(true);
            expect(result.current.canEdit('op-1')).toBe(true);
        });

        it('returns true for contributors on non-adminOnly extensions', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: ['ABC_BOOMI_FLOW_CONTRIBUTOR'],
                    isAdmin: false,
                }),
            );
            expect(result.current.canEdit('op-1')).toBe(true);
        });

        it('returns false for non-admins on adminOnly extensions', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: ['ABC_BOOMI_FLOW_CONTRIBUTOR'],
                    isAdmin: false,
                }),
            );
            // conn-2 is only in adminOnly process (proc-2)
            expect(result.current.canEdit('conn-2')).toBe(false);
        });

        it('returns false when user has no recognized groups', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: [],
                    isAdmin: false,
                }),
            );
            expect(result.current.canEdit('op-1')).toBe(false);
        });

        it('treats ABC_BOOMI_FLOW_ADMIN group same as isAdmin flag', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: ['ABC_BOOMI_FLOW_ADMIN'],
                    isAdmin: false,
                }),
            );
            expect(result.current.canEdit('conn-2')).toBe(true);
        });
    });

    describe('isConnectionExtension', () => {
        it('returns true for connection IDs', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: [],
                    isAdmin: false,
                }),
            );
            expect(result.current.isConnectionExtension('conn-1', connectionIds)).toBe(true);
            expect(result.current.isConnectionExtension('conn-2', connectionIds)).toBe(true);
        });

        it('returns false for non-connection IDs', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: [],
                    isAdmin: false,
                }),
            );
            expect(result.current.isConnectionExtension('op-1', connectionIds)).toBe(false);
            expect(result.current.isConnectionExtension('pp-1', connectionIds)).toBe(false);
        });
    });

    describe('getAuthorizedProcesses', () => {
        it('returns process names that include the extension', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: [],
                    isAdmin: false,
                }),
            );
            // pp-1 is used by both proc-1 and proc-2
            const processes = result.current.getAuthorizedProcesses('pp-1');
            expect(processes).toContain('Order Processing');
            expect(processes).toContain('SAP Integration');
            expect(processes).toHaveLength(2);
        });

        it('returns empty array for unknown extension', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: [],
                    isAdmin: false,
                }),
            );
            expect(result.current.getAuthorizedProcesses('unknown-ext')).toEqual([]);
        });

        it('returns single process for extension used by one process', () => {
            const { result } = renderHook(() =>
                useAccessControl({
                    accessMappings: sampleMappings,
                    userSsoGroups: [],
                    isAdmin: false,
                }),
            );
            expect(result.current.getAuthorizedProcesses('op-1')).toEqual(['Order Processing']);
        });
    });
});
