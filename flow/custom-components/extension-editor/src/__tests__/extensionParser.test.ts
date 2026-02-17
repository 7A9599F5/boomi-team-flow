/**
 * @jest-environment jsdom
 */
import { parseExtensionData, serializeExtensionData, parseAccessMappings, extractEditorData } from '../utils/extensionParser';
import { IObjectDataEntry } from '../types';

const sampleExtensionJson = JSON.stringify({
    accountId: 'ABC-PROD',
    environmentId: 'env-prod-001',
    environmentName: 'Production',
    connections: {
        'conn-abc-123': {
            name: 'Salesforce CRM',
            extensionGroupId: 'grp-sfdc',
            properties: {
                host: { name: 'Host', value: '', useDefault: true, encrypted: false },
                username: { name: 'Username', value: 'api@co.com', useDefault: false, encrypted: false },
            },
        },
    },
    operations: {},
    processProperties: {
        'pp-env-001': {
            name: 'BASE_URL',
            value: 'https://api.prod.co',
            useDefault: false,
            encrypted: false,
        },
    },
});

describe('parseExtensionData', () => {
    it('parses valid extension JSON', () => {
        const model = parseExtensionData(sampleExtensionJson);
        expect(model.accountId).toBe('ABC-PROD');
        expect(model.environmentId).toBe('env-prod-001');
        expect(model.environmentName).toBe('Production');
    });

    it('parses connections correctly', () => {
        const model = parseExtensionData(sampleExtensionJson);
        expect(Object.keys(model.connections)).toHaveLength(1);
        expect(model.connections['conn-abc-123'].name).toBe('Salesforce CRM');
        expect(model.connections['conn-abc-123'].properties['host'].useDefault).toBe(true);
    });

    it('parses process properties correctly', () => {
        const model = parseExtensionData(sampleExtensionJson);
        expect(model.processProperties['pp-env-001'].name).toBe('BASE_URL');
        expect(model.processProperties['pp-env-001'].value).toBe('https://api.prod.co');
    });

    it('throws on empty string', () => {
        expect(() => parseExtensionData('')).toThrow('Extension data is empty');
    });

    it('throws on invalid JSON', () => {
        expect(() => parseExtensionData('{not valid json')).toThrow('not valid JSON');
    });

    it('throws when environmentId is missing', () => {
        const bad = JSON.stringify({ accountId: 'ABC', connections: {}, operations: {}, processProperties: {} });
        expect(() => parseExtensionData(bad)).toThrow('environmentId');
    });

    it('returns empty records for missing section keys', () => {
        const minimal = JSON.stringify({ environmentId: 'env-1', accountId: 'ABC', environmentName: 'Test' });
        const model = parseExtensionData(minimal);
        expect(model.connections).toEqual({});
        expect(model.operations).toEqual({});
        expect(model.processProperties).toEqual({});
    });
});

describe('serializeExtensionData', () => {
    it('round-trips extension data', () => {
        const model = parseExtensionData(sampleExtensionJson);
        const serialized = serializeExtensionData(model);
        const reparsed = parseExtensionData(serialized);
        expect(reparsed.environmentId).toBe(model.environmentId);
        expect(reparsed.connections['conn-abc-123'].name).toBe(model.connections['conn-abc-123'].name);
    });

    it('outputs valid JSON', () => {
        const model = parseExtensionData(sampleExtensionJson);
        const serialized = serializeExtensionData(model);
        expect(() => JSON.parse(serialized)).not.toThrow();
    });
});

describe('parseAccessMappings', () => {
    const sampleMappings = JSON.stringify([
        { processId: 'proc-1', processName: 'Order Processing', extensionIds: ['conn-abc-123'], adminOnly: false },
        { processId: 'proc-2', processName: 'SAP Integration', extensionIds: ['conn-abc-123', 'pp-env-001'], adminOnly: true },
    ]);

    it('parses valid mappings', () => {
        const mappings = parseAccessMappings(sampleMappings);
        expect(mappings).toHaveLength(2);
        expect(mappings[0].processName).toBe('Order Processing');
        expect(mappings[1].adminOnly).toBe(true);
    });

    it('returns empty array for empty string', () => {
        expect(parseAccessMappings('')).toEqual([]);
    });

    it('returns empty array for invalid JSON', () => {
        expect(parseAccessMappings('{bad')).toEqual([]);
    });

    it('returns empty array for non-array JSON', () => {
        expect(parseAccessMappings('{"key": "value"}')).toEqual([]);
    });
});

describe('extractEditorData', () => {
    const makeObjectData = (
        extensionData: string,
        accessMappings: string,
        isAdmin = 'false',
        ssoGroups = 'ABC_BOOMI_FLOW_CONTRIBUTOR',
    ): IObjectDataEntry[] => [
        {
            internalId: 'id-1',
            externalId: 'ext-1',
            developerName: 'ExtensionEditorData',
            properties: [
                { developerName: 'extensionData', contentValue: extensionData, contentType: 'ContentString', objectData: null },
                { developerName: 'accessMappings', contentValue: accessMappings, contentType: 'ContentString', objectData: null },
                { developerName: 'isAdmin', contentValue: isAdmin, contentType: 'ContentBoolean', objectData: null },
                { developerName: 'userSsoGroups', contentValue: ssoGroups, contentType: 'ContentString', objectData: null },
            ],
        },
    ];

    it('extracts all fields from valid objectData', () => {
        const result = extractEditorData(makeObjectData(sampleExtensionJson, '[]'));
        expect(result.parseError).toBeNull();
        expect(result.extensionData).not.toBeNull();
        expect(result.extensionData?.environmentId).toBe('env-prod-001');
    });

    it('sets parseError when extensionData JSON is invalid', () => {
        const result = extractEditorData(makeObjectData('{bad', '[]'));
        expect(result.parseError).not.toBeNull();
        expect(result.extensionData).toBeNull();
    });

    it('sets isAdmin true when flag is "true"', () => {
        const result = extractEditorData(makeObjectData(sampleExtensionJson, '[]', 'true'));
        expect(result.isAdmin).toBe(true);
    });

    it('sets isAdmin false for "false"', () => {
        const result = extractEditorData(makeObjectData(sampleExtensionJson, '[]', 'false'));
        expect(result.isAdmin).toBe(false);
    });

    it('splits ssoGroups by comma', () => {
        const result = extractEditorData(
            makeObjectData(sampleExtensionJson, '[]', 'false', 'ABC_BOOMI_FLOW_CONTRIBUTOR,ABC_BOOMI_FLOW_ADMIN'),
        );
        expect(result.userSsoGroups).toEqual(['ABC_BOOMI_FLOW_CONTRIBUTOR', 'ABC_BOOMI_FLOW_ADMIN']);
    });

    it('returns error when objectData is null', () => {
        const result = extractEditorData(null);
        expect(result.parseError).toBe('No data provided');
    });

    it('returns error when objectData is empty array', () => {
        const result = extractEditorData([]);
        expect(result.parseError).toBe('No data provided');
    });
});
