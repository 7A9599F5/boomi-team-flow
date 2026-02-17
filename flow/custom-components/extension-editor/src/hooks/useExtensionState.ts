import { useReducer, useCallback } from 'react';
import {
    IExtensionEditorState,
    IExtensionModel,
    ExtensionEditorAction,
    IFieldEdit,
} from '../types';

const MAX_UNDO_HISTORY = 50;

/** Initial state for the extension editor */
const initialState: IExtensionEditorState = {
    extensionData: null,
    editedFields: {},
    undoStack: [],
    redoStack: [],
    selectedNodeId: null,
    searchQuery: '',
    parseError: null,
};

/**
 * Build a composite key for a field edit record.
 */
function fieldKey(extensionId: string, propertyKey: string): string {
    return `${extensionId}::${propertyKey}`;
}

/**
 * Extension editor reducer — handles edit state, undo/redo, selection.
 */
function extensionEditorReducer(
    state: IExtensionEditorState,
    action: ExtensionEditorAction,
): IExtensionEditorState {
    switch (action.type) {
        case 'LOAD_DATA': {
            return {
                ...initialState,
                extensionData: action.payload,
            };
        }

        case 'LOAD_ERROR': {
            return {
                ...initialState,
                parseError: action.payload,
            };
        }

        case 'SET_VALUE': {
            const { extensionId, propertyKey, value } = action.payload;
            const key = fieldKey(extensionId, propertyKey);
            const prevEdit = state.editedFields[key];

            // Snapshot current edits for undo
            const snapshot = Object.values(state.editedFields);
            const newUndoStack = [
                ...state.undoStack.slice(-(MAX_UNDO_HISTORY - 1)),
                snapshot,
            ];

            const newEdit: IFieldEdit = {
                extensionId,
                propertyKey,
                value,
                useDefault: prevEdit?.useDefault ?? false,
            };

            return {
                ...state,
                editedFields: {
                    ...state.editedFields,
                    [key]: newEdit,
                },
                undoStack: newUndoStack,
                redoStack: [],
            };
        }

        case 'TOGGLE_DEFAULT': {
            const { extensionId, propertyKey, useDefault } = action.payload;
            const key = fieldKey(extensionId, propertyKey);
            const prevEdit = state.editedFields[key];

            const snapshot = Object.values(state.editedFields);
            const newUndoStack = [
                ...state.undoStack.slice(-(MAX_UNDO_HISTORY - 1)),
                snapshot,
            ];

            const newEdit: IFieldEdit = {
                extensionId,
                propertyKey,
                value: prevEdit?.value ?? '',
                useDefault,
            };

            return {
                ...state,
                editedFields: {
                    ...state.editedFields,
                    [key]: newEdit,
                },
                undoStack: newUndoStack,
                redoStack: [],
            };
        }

        case 'SELECT_NODE': {
            return {
                ...state,
                selectedNodeId: action.payload,
            };
        }

        case 'SET_SEARCH': {
            return {
                ...state,
                searchQuery: action.payload,
            };
        }

        case 'UNDO': {
            if (state.undoStack.length === 0) return state;

            const prevSnapshot = state.undoStack[state.undoStack.length - 1];
            const currentSnapshot = Object.values(state.editedFields);

            // Rebuild editedFields from the snapshot
            const restored: Record<string, IFieldEdit> = {};
            for (const edit of prevSnapshot) {
                restored[fieldKey(edit.extensionId, edit.propertyKey)] = edit;
            }

            return {
                ...state,
                editedFields: restored,
                undoStack: state.undoStack.slice(0, -1),
                redoStack: [
                    ...state.redoStack.slice(-(MAX_UNDO_HISTORY - 1)),
                    currentSnapshot,
                ],
            };
        }

        case 'REDO': {
            if (state.redoStack.length === 0) return state;

            const nextSnapshot = state.redoStack[state.redoStack.length - 1];
            const currentSnapshot = Object.values(state.editedFields);

            const restored: Record<string, IFieldEdit> = {};
            for (const edit of nextSnapshot) {
                restored[fieldKey(edit.extensionId, edit.propertyKey)] = edit;
            }

            return {
                ...state,
                editedFields: restored,
                undoStack: [
                    ...state.undoStack.slice(-(MAX_UNDO_HISTORY - 1)),
                    currentSnapshot,
                ],
                redoStack: state.redoStack.slice(0, -1),
            };
        }

        case 'RESET': {
            return {
                ...state,
                editedFields: {},
                undoStack: [],
                redoStack: [],
            };
        }

        default:
            return state;
    }
}

/**
 * Returns the number of distinct (extensionId, propertyKey) pairs that have edits.
 */
function getDirtyFieldCount(editedFields: Record<string, IFieldEdit>): number {
    return Object.keys(editedFields).length;
}

/**
 * Returns the list of changed IFieldEdit records.
 */
function getChangedFields(editedFields: Record<string, IFieldEdit>): IFieldEdit[] {
    return Object.values(editedFields);
}

/**
 * Hook for managing extension editor state with undo/redo support.
 *
 * Uses useReducer to handle a rich edit state including:
 * - SET_VALUE / TOGGLE_DEFAULT for individual field edits
 * - UNDO / REDO for up to 50-level history
 * - LOAD_DATA to initialize from parsed extension JSON
 * - RESET to clear all edits
 */
export function useExtensionState() {
    const [state, dispatch] = useReducer(extensionEditorReducer, initialState);

    const loadData = useCallback((data: IExtensionModel) => {
        dispatch({ type: 'LOAD_DATA', payload: data });
    }, []);

    const loadError = useCallback((error: string) => {
        dispatch({ type: 'LOAD_ERROR', payload: error });
    }, []);

    const setValue = useCallback(
        (extensionId: string, propertyKey: string, value: string) => {
            dispatch({ type: 'SET_VALUE', payload: { extensionId, propertyKey, value } });
        },
        [],
    );

    const toggleDefault = useCallback(
        (extensionId: string, propertyKey: string, useDefault: boolean) => {
            dispatch({ type: 'TOGGLE_DEFAULT', payload: { extensionId, propertyKey, useDefault } });
        },
        [],
    );

    const selectNode = useCallback((nodeId: string | null) => {
        dispatch({ type: 'SELECT_NODE', payload: nodeId });
    }, []);

    const setSearch = useCallback((query: string) => {
        dispatch({ type: 'SET_SEARCH', payload: query });
    }, []);

    const undo = useCallback(() => {
        dispatch({ type: 'UNDO' });
    }, []);

    const redo = useCallback(() => {
        dispatch({ type: 'REDO' });
    }, []);

    const reset = useCallback(() => {
        dispatch({ type: 'RESET' });
    }, []);

    return {
        state,
        loadData,
        loadError,
        setValue,
        toggleDefault,
        selectNode,
        setSearch,
        undo,
        redo,
        reset,
        dirtyFieldCount: getDirtyFieldCount(state.editedFields),
        changedFields: getChangedFields(state.editedFields),
        canUndo: state.undoStack.length > 0,
        canRedo: state.redoStack.length > 0,
    };
}
