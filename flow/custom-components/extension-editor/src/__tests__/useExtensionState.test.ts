/**
 * @jest-environment jsdom
 */
import { renderHook, act } from '@testing-library/react-hooks';
import { useExtensionState } from '../hooks/useExtensionState';
import { IExtensionModel } from '../types';

const sampleModel: IExtensionModel = {
    accountId: 'ABC-PROD',
    environmentId: 'env-prod-001',
    environmentName: 'Production',
    connections: {
        'conn-1': {
            name: 'CRM Connection',
            extensionGroupId: 'grp-1',
            properties: {
                host: { name: 'Host', value: 'old.server.com', useDefault: false, encrypted: false },
            },
        },
    },
    operations: {},
    processProperties: {
        'pp-1': { name: 'BASE_URL', value: 'https://old.api.com', useDefault: false, encrypted: false },
    },
};

describe('useExtensionState', () => {
    it('initializes with null extensionData', () => {
        const { result } = renderHook(() => useExtensionState());
        expect(result.current.state.extensionData).toBeNull();
    });

    it('loads data via loadData', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => {
            result.current.loadData(sampleModel);
        });
        expect(result.current.state.extensionData?.environmentId).toBe('env-prod-001');
        expect(result.current.state.editedFields).toEqual({});
    });

    it('records field edits via setValue', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'new.server.com'));

        expect(result.current.dirtyFieldCount).toBe(1);
        const key = 'conn-1::host';
        expect(result.current.state.editedFields[key].value).toBe('new.server.com');
    });

    it('records toggle default via toggleDefault', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.toggleDefault('conn-1', 'host', true));

        const key = 'conn-1::host';
        expect(result.current.state.editedFields[key].useDefault).toBe(true);
        expect(result.current.dirtyFieldCount).toBe(1);
    });

    it('supports undo', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'v1.server.com'));
        act(() => result.current.setValue('conn-1', 'host', 'v2.server.com'));

        expect(result.current.state.editedFields['conn-1::host'].value).toBe('v2.server.com');

        act(() => result.current.undo());
        expect(result.current.state.editedFields['conn-1::host'].value).toBe('v1.server.com');
    });

    it('supports redo after undo', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'v1.server.com'));
        act(() => result.current.setValue('conn-1', 'host', 'v2.server.com'));
        act(() => result.current.undo());
        act(() => result.current.redo());

        expect(result.current.state.editedFields['conn-1::host'].value).toBe('v2.server.com');
    });

    it('clears redo stack on new edit after undo', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'v1'));
        act(() => result.current.setValue('conn-1', 'host', 'v2'));
        act(() => result.current.undo());
        expect(result.current.canRedo).toBe(true);

        // New edit clears redo stack
        act(() => result.current.setValue('conn-1', 'host', 'v3'));
        expect(result.current.canRedo).toBe(false);
    });

    it('canUndo is false before any edits', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        expect(result.current.canUndo).toBe(false);
    });

    it('canRedo is false before any undo', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'v1'));
        expect(result.current.canRedo).toBe(false);
    });

    it('reset clears all edits and history', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'new.server.com'));
        act(() => result.current.reset());

        expect(result.current.dirtyFieldCount).toBe(0);
        expect(result.current.canUndo).toBe(false);
        expect(result.current.canRedo).toBe(false);
    });

    it('selectNode sets selectedNodeId', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.selectNode('connections::conn-1'));
        expect(result.current.state.selectedNodeId).toBe('connections::conn-1');
    });

    it('setSearch sets searchQuery', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.setSearch('Salesforce'));
        expect(result.current.state.searchQuery).toBe('Salesforce');
    });

    it('loadError sets parseError', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadError('Failed to parse JSON'));
        expect(result.current.state.parseError).toBe('Failed to parse JSON');
    });

    it('changedFields returns array of all edits', () => {
        const { result } = renderHook(() => useExtensionState());
        act(() => result.current.loadData(sampleModel));
        act(() => result.current.setValue('conn-1', 'host', 'v1'));

        expect(result.current.changedFields).toHaveLength(1);
        expect(result.current.changedFields[0].extensionId).toBe('conn-1');
        expect(result.current.changedFields[0].propertyKey).toBe('host');
        expect(result.current.changedFields[0].value).toBe('v1');
    });
});
