import {
    IExtensionModel,
    IExtensionGroup,
    IExtensionProperty,
    IProcessProperty,
    IObjectDataEntry,
    IObjectDataProperty,
    IAccessMapping,
} from '../types';

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
 * Validate that a value is a non-null object (not array).
 */
function isPlainObject(val: unknown): val is Record<string, unknown> {
    return typeof val === 'object' && val !== null && !Array.isArray(val);
}

/**
 * Safely coerce to string.
 */
function toStr(val: unknown): string {
    if (typeof val === 'string') return val;
    if (typeof val === 'number' || typeof val === 'boolean') return String(val);
    return '';
}

/**
 * Parse a raw properties map into typed IExtensionProperty records.
 */
function parseProperties(
    raw: unknown,
): Record<string, IExtensionProperty> {
    if (!isPlainObject(raw)) return {};
    const result: Record<string, IExtensionProperty> = {};
    for (const [key, val] of Object.entries(raw)) {
        if (!isPlainObject(val)) continue;
        result[key] = {
            name: toStr(val['name']),
            value: toStr(val['value']),
            useDefault: val['useDefault'] === true,
            encrypted: val['encrypted'] === true,
        };
    }
    return result;
}

/**
 * Parse a raw connections or operations map into typed IExtensionGroup records.
 */
function parseExtensionGroups(
    raw: unknown,
): Record<string, IExtensionGroup> {
    if (!isPlainObject(raw)) return {};
    const result: Record<string, IExtensionGroup> = {};
    for (const [key, val] of Object.entries(raw)) {
        if (!isPlainObject(val)) continue;
        result[key] = {
            name: toStr(val['name']),
            extensionGroupId: toStr(val['extensionGroupId']),
            properties: parseProperties(val['properties']),
        };
    }
    return result;
}

/**
 * Parse a raw processProperties map into typed IProcessProperty records.
 */
function parseProcessProperties(
    raw: unknown,
): Record<string, IProcessProperty> {
    if (!isPlainObject(raw)) return {};
    const result: Record<string, IProcessProperty> = {};
    for (const [key, val] of Object.entries(raw)) {
        if (!isPlainObject(val)) continue;
        result[key] = {
            name: toStr(val['name']),
            value: toStr(val['value']),
            useDefault: val['useDefault'] === true,
            encrypted: val['encrypted'] === true,
        };
    }
    return result;
}

/**
 * Parse a JSON string of EnvironmentExtensions data into a typed IExtensionModel.
 * Throws if the JSON is invalid or required fields are missing.
 */
export function parseExtensionData(jsonString: string): IExtensionModel {
    if (!jsonString || !jsonString.trim()) {
        throw new Error('Extension data is empty');
    }

    let raw: unknown;
    try {
        raw = JSON.parse(jsonString);
    } catch (e) {
        throw new Error('Extension data is not valid JSON');
    }

    if (!isPlainObject(raw)) {
        throw new Error('Extension data must be a JSON object');
    }

    if (!raw['environmentId'] || typeof raw['environmentId'] !== 'string') {
        throw new Error('Extension data missing required field: environmentId');
    }

    return {
        accountId: toStr(raw['accountId']),
        environmentId: toStr(raw['environmentId']),
        environmentName: toStr(raw['environmentName']),
        connections: parseExtensionGroups(raw['connections']),
        operations: parseExtensionGroups(raw['operations']),
        processProperties: parseProcessProperties(raw['processProperties']),
        crossReferenceOverrides: isPlainObject(raw['crossReferenceOverrides'])
            ? Object.fromEntries(
                Object.entries(raw['crossReferenceOverrides']).map(
                    ([k, v]) => [k, toStr(v)],
                ),
              )
            : undefined,
    };
}

/**
 * Serialize a typed IExtensionModel back to a JSON string.
 */
export function serializeExtensionData(model: IExtensionModel): string {
    return JSON.stringify(model, null, 2);
}

/**
 * Parse access mappings JSON string into typed IAccessMapping array.
 */
export function parseAccessMappings(jsonString: string): IAccessMapping[] {
    if (!jsonString || !jsonString.trim()) {
        return [];
    }

    let raw: unknown;
    try {
        raw = JSON.parse(jsonString);
    } catch {
        return [];
    }

    if (!Array.isArray(raw)) return [];

    return raw
        .filter(isPlainObject)
        .map((item) => ({
            processId: toStr(item['processId']),
            processName: toStr(item['processName']),
            extensionIds: Array.isArray(item['extensionIds'])
                ? (item['extensionIds'] as unknown[]).map(toStr)
                : [],
            adminOnly: item['adminOnly'] === true,
        }));
}

/**
 * Extract typed editor data from the first objectData entry.
 * Returns null if objectData is missing or empty.
 */
export function extractEditorData(
    objectData: IObjectDataEntry[] | null | undefined,
): {
    extensionData: IExtensionModel | null;
    accessMappings: IAccessMapping[];
    isAdmin: boolean;
    userSsoGroups: string[];
    parseError: string | null;
} {
    if (!objectData || objectData.length === 0) {
        return {
            extensionData: null,
            accessMappings: [],
            isAdmin: false,
            userSsoGroups: [],
            parseError: 'No data provided',
        };
    }

    const entry = objectData[0];
    const extensionJson = getPropertyValue(entry, 'extensionData');
    const accessJson = getPropertyValue(entry, 'accessMappings');
    const isAdminStr = getPropertyValue(entry, 'isAdmin');
    const ssoGroupsStr = getPropertyValue(entry, 'userSsoGroups');

    let extensionData: IExtensionModel | null = null;
    let parseError: string | null = null;

    try {
        extensionData = parseExtensionData(extensionJson);
    } catch (e) {
        parseError = e instanceof Error ? e.message : 'Failed to parse extension data';
    }

    const accessMappings = parseAccessMappings(accessJson);
    const isAdmin = isAdminStr === 'true' || isAdminStr === '1';
    const userSsoGroups = ssoGroupsStr
        ? ssoGroupsStr.split(',').map((g) => g.trim()).filter(Boolean)
        : [];

    return { extensionData, accessMappings, isAdmin, userSsoGroups, parseError };
}
