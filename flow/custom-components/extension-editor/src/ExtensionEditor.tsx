import * as React from 'react';
import { useState, useEffect, useCallback, useMemo } from 'react';
import { IWrappedComponentProps } from './utils/wrapper';
import { extractEditorData, serializeExtensionData } from './utils/extensionParser';
import { useExtensionState } from './hooks/useExtensionState';
import { useAccessControl } from './hooks/useAccessControl';
import { IExtensionModel, IExtensionProperty, IFieldEdit, ExtensionCategory } from './types';
import { ExtensionTree } from './components/ExtensionTree';
import { PropertyTable } from './components/PropertyTable';
import { SearchBar } from './components/SearchBar';
import { EnvironmentSelector } from './components/EnvironmentSelector';
import { SaveToolbar } from './components/SaveToolbar';
import { SharedResourceBanner } from './components/SharedResourceBanner';
import { DppBanner } from './components/DppBanner';
import { ConnectionBanner } from './components/ConnectionBanner';
import { ConfirmationDialog } from './components/ConfirmationDialog';
import './styles/extension-editor.css';

/**
 * Derive the category from a node ID of the form "category::extensionId".
 */
function parseCategoryFromNodeId(nodeId: string): ExtensionCategory | null {
    const sep = nodeId.indexOf('::');
    if (sep < 0) return null;
    return nodeId.slice(0, sep) as ExtensionCategory;
}

/**
 * Derive the extension ID from a node ID of the form "category::extensionId".
 */
function parseExtensionIdFromNodeId(nodeId: string): string {
    const sep = nodeId.indexOf('::');
    if (sep < 0) return nodeId;
    return nodeId.slice(sep + 2);
}

/**
 * Apply all pending field edits onto an IExtensionModel to produce the saved version.
 */
function applyEdits(model: IExtensionModel, edits: IFieldEdit[]): IExtensionModel {
    const result: IExtensionModel = JSON.parse(JSON.stringify(model));

    for (const edit of edits) {
        const { extensionId, propertyKey, value, useDefault } = edit;

        if (result.connections[extensionId]?.properties[propertyKey] !== undefined) {
            result.connections[extensionId].properties[propertyKey].value = value;
            result.connections[extensionId].properties[propertyKey].useDefault = useDefault;
        } else if (result.operations[extensionId]?.properties[propertyKey] !== undefined) {
            result.operations[extensionId].properties[propertyKey].value = value;
            result.operations[extensionId].properties[propertyKey].useDefault = useDefault;
        } else if (result.processProperties[extensionId] !== undefined && propertyKey === 'value') {
            result.processProperties[extensionId].value = value;
            result.processProperties[extensionId].useDefault = useDefault;
        }
    }

    return result;
}

/**
 * Simple error boundary for the extension editor.
 */
class ExtensionEditorErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { error: Error | null }
> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error: Error) {
        return { error };
    }

    render() {
        if (this.state.error) {
            return (
                <div className="ee-error" role="alert">
                    <div className="ee-error__icon" aria-hidden="true">!</div>
                    <p className="ee-error__message">
                        Extension editor encountered an error:{' '}
                        {this.state.error.message}
                    </p>
                </div>
            );
        }
        return this.props.children;
    }
}

/**
 * ExtensionEditor — main orchestrator component for Boomi Flow.
 *
 * Receives objectData from Flow runtime via HOC wrapper. Parses extension JSON
 * and access mapping data, then renders a two-panel editor: ExtensionTree (left)
 * and PropertyTable (right). Save/Undo/Redo toolbar at bottom.
 *
 * Manages edit state via useExtensionState (useReducer-based with undo/redo).
 * Permission checks via useAccessControl.
 */
export const ExtensionEditor: React.FC<IWrappedComponentProps> = ({
    objectData,
    state,
}) => {
    const {
        state: editorState,
        loadData,
        loadError,
        setValue,
        toggleDefault,
        selectNode,
        setSearch,
        undo,
        redo,
        reset,
        dirtyFieldCount,
        changedFields,
        canUndo,
        canRedo,
    } = useExtensionState();

    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const [pendingSave, setPendingSave] = useState(false);

    // Extract and parse data from objectData on mount / when objectData changes
    useEffect(() => {
        if (state?.loading) return;
        if (!objectData || objectData.length === 0) {
            loadError('No extension data provided');
            return;
        }

        const { extensionData, accessMappings, isAdmin, userSsoGroups, parseError } =
            extractEditorData(objectData);

        if (parseError || !extensionData) {
            loadError(parseError ?? 'Failed to parse extension data');
            return;
        }

        loadData(extensionData);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [objectData, state?.loading]);

    // Re-parse accessMappings and user context from objectData
    const { accessMappings, isAdmin, userSsoGroups } = useMemo(() => {
        if (!objectData || objectData.length === 0) {
            return { accessMappings: [], isAdmin: false, userSsoGroups: [] };
        }
        const parsed = extractEditorData(objectData);
        return {
            accessMappings: parsed.accessMappings,
            isAdmin: parsed.isAdmin,
            userSsoGroups: parsed.userSsoGroups,
        };
    }, [objectData]);

    const accessControl = useAccessControl({ accessMappings, userSsoGroups, isAdmin });

    // Compute connection IDs set for permission checking
    const connectionIds = useMemo<Set<string>>(() => {
        if (!editorState.extensionData) return new Set();
        return new Set(Object.keys(editorState.extensionData.connections));
    }, [editorState.extensionData]);

    // Determine properties for the currently selected node
    const selectedProperties = useMemo<Record<string, IExtensionProperty> | null>(() => {
        const { selectedNodeId, extensionData } = editorState;
        if (!selectedNodeId || !extensionData) return null;

        const extId = parseExtensionIdFromNodeId(selectedNodeId);
        const category = parseCategoryFromNodeId(selectedNodeId);

        if (category === 'connections') {
            return extensionData.connections[extId]?.properties ?? null;
        }
        if (category === 'operations') {
            return extensionData.operations[extId]?.properties ?? null;
        }
        if (category === 'processProperties') {
            const pp = extensionData.processProperties[extId];
            if (!pp) return null;
            // Normalize process property to the same Record<string, IExtensionProperty> shape
            return {
                value: {
                    name: pp.name,
                    value: pp.value,
                    useDefault: pp.useDefault,
                    encrypted: pp.encrypted,
                },
            };
        }
        return null;
    }, [editorState.selectedNodeId, editorState.extensionData]);

    // Get shared process names for the selected extension
    const sharedProcessNames = useMemo<string[]>(() => {
        const { selectedNodeId } = editorState;
        if (!selectedNodeId) return [];
        const extId = parseExtensionIdFromNodeId(selectedNodeId);
        return accessControl.getAuthorizedProcesses(extId);
    }, [editorState.selectedNodeId, accessControl]);

    const selectedExtId = editorState.selectedNodeId
        ? parseExtensionIdFromNodeId(editorState.selectedNodeId)
        : null;
    const selectedCategory = editorState.selectedNodeId
        ? parseCategoryFromNodeId(editorState.selectedNodeId)
        : null;

    const selectedCanEdit = selectedExtId
        ? accessControl.canEdit(selectedExtId) &&
          !accessControl.isConnectionExtension(selectedExtId, connectionIds)
        : false;

    const isSelectedConnection = selectedExtId
        ? accessControl.isConnectionExtension(selectedExtId, connectionIds)
        : false;

    const handleSaveRequest = useCallback(() => {
        if (sharedProcessNames.length >= 2) {
            setShowConfirmDialog(true);
            setPendingSave(true);
        } else {
            // Direct save — no confirmation needed
            executeSave();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sharedProcessNames, changedFields, editorState.extensionData]);

    const executeSave = useCallback(() => {
        if (!editorState.extensionData) return;
        const updated = applyEdits(editorState.extensionData, changedFields);
        const serialized = serializeExtensionData(updated);
        // In a real Flow integration, write serialized back to a Flow value
        // and trigger the "Save" outcome. For this spec, we log the output.
        console.log('[ExtensionEditor] Save payload:', serialized);
        reset();
        setShowConfirmDialog(false);
        setPendingSave(false);
    }, [editorState.extensionData, changedFields, reset]);

    const handleConfirmSave = useCallback(() => {
        executeSave();
    }, [executeSave]);

    const handleCancelSave = useCallback(() => {
        setShowConfirmDialog(false);
        setPendingSave(false);
    }, []);

    const handleCopyTestToProd = useCallback(() => {
        // Triggers "CopyTestToProd" outcome — navigates to Page 11 in Flow
        console.log('[ExtensionEditor] CopyTestToProd outcome triggered');
    }, []);

    // Loading state
    if (state?.loading) {
        return (
            <div className="extension-editor extension-editor--loading" role="status">
                <div className="ee-loading__skeleton ee-loading__skeleton--header" />
                <div className="ee-loading__panels">
                    <div className="ee-loading__skeleton ee-loading__skeleton--tree" />
                    <div className="ee-loading__skeleton ee-loading__skeleton--table" />
                </div>
            </div>
        );
    }

    // Parse/data error state
    if (editorState.parseError || !editorState.extensionData) {
        return (
            <div className="extension-editor">
                <div className="ee-error" role="alert">
                    <div className="ee-error__icon" aria-hidden="true">!</div>
                    <p className="ee-error__message">
                        {editorState.parseError ?? 'No extension data available'}
                    </p>
                </div>
            </div>
        );
    }

    return (
        <ExtensionEditorErrorBoundary>
            <div className="extension-editor">
                {/* Top: Environment selector */}
                <EnvironmentSelector
                    accounts={[
                        {
                            id: editorState.extensionData.accountId,
                            name: editorState.extensionData.accountId,
                        },
                    ]}
                    selectedAccountId={editorState.extensionData.accountId}
                    environments={[
                        {
                            id: editorState.extensionData.environmentId,
                            name: editorState.extensionData.environmentName,
                        },
                    ]}
                    selectedEnvironmentId={editorState.extensionData.environmentId}
                    onAccountChange={() => { /* reload data via outcome */ }}
                    onEnvironmentChange={() => { /* reload data via outcome */ }}
                />

                {/* Search bar */}
                <SearchBar
                    value={editorState.searchQuery}
                    onChange={setSearch}
                />

                {/* Two-panel layout */}
                <div className="ee-panels">
                    {/* Left: Extension tree */}
                    <div className="ee-panels__tree">
                        <ExtensionTree
                            extensionData={editorState.extensionData}
                            accessMappings={accessMappings}
                            selectedNodeId={editorState.selectedNodeId}
                            searchQuery={editorState.searchQuery}
                            isAdmin={isAdmin}
                            onSelectNode={selectNode}
                        />
                    </div>

                    {/* Right: Property table */}
                    <div className="ee-panels__properties">
                        {/* Context banners */}
                        {isSelectedConnection && (
                            <ConnectionBanner canEdit={isAdmin} />
                        )}
                        {selectedCategory === 'processProperties' && (
                            <DppBanner />
                        )}
                        {sharedProcessNames.length >= 2 && (
                            <SharedResourceBanner processNames={sharedProcessNames} />
                        )}

                        {/* Property table */}
                        {selectedProperties ? (
                            <PropertyTable
                                extensionId={selectedExtId ?? ''}
                                properties={selectedProperties}
                                editedFields={editorState.editedFields}
                                canEdit={selectedCanEdit}
                                onSetValue={setValue}
                                onToggleDefault={toggleDefault}
                            />
                        ) : (
                            <div className="ee-panels__no-selection">
                                <p>Select an extension from the tree to view its properties.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Bottom: Save toolbar */}
                <SaveToolbar
                    dirtyFieldCount={dirtyFieldCount}
                    canUndo={canUndo}
                    canRedo={canRedo}
                    canSave={!isSelectedConnection || isAdmin}
                    hasTestEnvironment={false}
                    onSave={handleSaveRequest}
                    onUndo={undo}
                    onRedo={redo}
                    onCopyTestToProd={handleCopyTestToProd}
                />

                {/* Confirmation dialog for shared extension saves */}
                <ConfirmationDialog
                    isOpen={showConfirmDialog}
                    affectedProcesses={sharedProcessNames}
                    onConfirm={handleConfirmSave}
                    onCancel={handleCancelSave}
                />
            </div>
        </ExtensionEditorErrorBoundary>
    );
};
