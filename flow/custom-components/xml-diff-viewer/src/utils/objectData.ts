import { IObjectDataEntry, IObjectDataProperty, IDiffData } from '../types';

/**
 * Get a named property value from a Flow objectData entry.
 * Returns the contentValue as string, or empty string if not found.
 */
export function getPropertyValue(
    entry: IObjectDataEntry,
    propertyName: string,
): string {
    const prop = entry.properties.find(
        (p: IObjectDataProperty) => p.developerName === propertyName,
    );
    return prop?.contentValue ?? '';
}

/**
 * Extract typed diff data from the first objectData entry.
 * Returns null if objectData is missing or empty.
 */
export function extractDiffData(
    objectData: IObjectDataEntry[] | null | undefined,
): IDiffData | null {
    if (!objectData || objectData.length === 0) {
        return null;
    }

    const entry = objectData[0];

    const branchXml = getPropertyValue(entry, 'branchXml');
    const mainXml = getPropertyValue(entry, 'mainXml');
    const componentName = getPropertyValue(entry, 'componentName');
    const componentAction = getPropertyValue(entry, 'componentAction');
    const branchVersion = getPropertyValue(entry, 'branchVersion');
    const mainVersion = getPropertyValue(entry, 'mainVersion');

    if (!branchXml || !componentName || !componentAction) {
        return null;
    }

    return {
        branchXml,
        mainXml,
        componentName,
        componentAction: componentAction as IDiffData['componentAction'],
        branchVersion: parseInt(branchVersion, 10) || 0,
        mainVersion: parseInt(mainVersion, 10) || 0,
    };
}
