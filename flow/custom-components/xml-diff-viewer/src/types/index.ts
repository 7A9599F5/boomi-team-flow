/** View mode for the diff display */
export type ViewMode = 'split' | 'unified';

/** Toolbar state managed by the main component */
export interface IToolbarState {
    viewMode: ViewMode;
    expandAll: boolean;
    wrapLines: boolean;
}

/** Computed diff statistics */
export interface IDiffStats {
    additions: number;
    deletions: number;
    unchanged: number;
}

/** Parsed diff data extracted from Flow objectData */
export interface IDiffData {
    branchXml: string;
    mainXml: string;
    componentName: string;
    componentAction: 'CREATE' | 'UPDATE';
    branchVersion: number;
    mainVersion: number;
}

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

/** Responsive breakpoint */
export type Breakpoint = 'desktop' | 'tablet' | 'mobile';
