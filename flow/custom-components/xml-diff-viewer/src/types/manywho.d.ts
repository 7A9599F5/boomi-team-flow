/** Type declarations for the Boomi Flow manywho global runtime */

interface ManywhoComponentModel {
    isVisible: boolean;
    isEnabled: boolean;
    attributes: Record<string, string>;
    objectData: import('./index').IObjectDataEntry[] | null;
    objectDataRequest: unknown;
    contentType: string;
    label: string;
    developerName: string;
}

interface ManywhoComponentState {
    loading: boolean;
    error: unknown;
    objectData: import('./index').IObjectDataEntry[] | null;
}

interface ManywhoComponent {
    register(name: string, component: React.ComponentType<any>): void;
    getByName(name: string): React.ComponentType<any> | undefined;
}

interface ManywhoModel {
    getComponent(id: string, flowKey: string): ManywhoComponentModel;
}

interface ManywhoState {
    getComponent(id: string, flowKey: string): ManywhoComponentState;
}

interface ManywhoStyling {
    getClasses(
        parentId: string,
        id: string,
        componentType: string,
        flowKey: string,
    ): string[];
}

interface Manywho {
    component: ManywhoComponent;
    model: ManywhoModel;
    state: ManywhoState;
    styling: ManywhoStyling;
}

declare const manywho: Manywho;
