/** A single property within an extension (connection, operation, processProperty) */
export interface IExtensionProperty {
    name: string;
    value: string;
    useDefault: boolean;
    encrypted: boolean;
}

/** A connection or operation extension group */
export interface IExtensionGroup {
    name: string;
    extensionGroupId: string;
    properties: Record<string, IExtensionProperty>;
}

/** A process property extension (environment-wide, not grouped) */
export interface IProcessProperty {
    name: string;
    value: string;
    useDefault: boolean;
    encrypted: boolean;
}

/** Top-level parsed extension data from Boomi EnvironmentExtensions API */
export interface IExtensionModel {
    accountId: string;
    environmentId: string;
    environmentName: string;
    connections: Record<string, IExtensionGroup>;
    operations: Record<string, IExtensionGroup>;
    processProperties: Record<string, IProcessProperty>;
    crossReferenceOverrides?: Record<string, string>;
}

/** A process-to-extension access mapping entry */
export interface IAccessMapping {
    processId: string;
    processName: string;
    extensionIds: string[];
    adminOnly: boolean;
}

/** Categories of extensions shown in the tree */
export type ExtensionCategory = 'connections' | 'operations' | 'processProperties' | 'crossReferenceOverrides';

/** A tree node representing an item in the extension tree */
export interface ITreeNode {
    id: string;
    label: string;
    category: ExtensionCategory;
    processId?: string;
    processName?: string;
    isShared: boolean;
    sharedByProcesses: string[];
    isConnectionExtension: boolean;
    isDppExtension: boolean;
}

/** Edit state for a single field */
export interface IFieldEdit {
    extensionId: string;
    propertyKey: string;
    value: string;
    useDefault: boolean;
}

/** Full reducer state for the extension editor */
export interface IExtensionEditorState {
    extensionData: IExtensionModel | null;
    editedFields: Record<string, IFieldEdit>;
    undoStack: IFieldEdit[][];
    redoStack: IFieldEdit[][];
    selectedNodeId: string | null;
    searchQuery: string;
    parseError: string | null;
}

/** Actions for the extension editor reducer */
export type ExtensionEditorAction =
    | { type: 'LOAD_DATA'; payload: IExtensionModel }
    | { type: 'LOAD_ERROR'; payload: string }
    | { type: 'SET_VALUE'; payload: { extensionId: string; propertyKey: string; value: string } }
    | { type: 'TOGGLE_DEFAULT'; payload: { extensionId: string; propertyKey: string; useDefault: boolean } }
    | { type: 'SELECT_NODE'; payload: string | null }
    | { type: 'SET_SEARCH'; payload: string }
    | { type: 'UNDO' }
    | { type: 'REDO' }
    | { type: 'RESET' };

/** A single property in a Flow objectData entry */
export interface IObjectDataProperty {
    developerName: string;
    contentValue: string | null;
    contentType: string;
    objectData: IObjectDataEntry[] | null;
}

/** A single entry in Flow objectData */
export interface IObjectDataEntry {
    internalId: string;
    externalId: string;
    developerName: string;
    properties: IObjectDataProperty[];
}
