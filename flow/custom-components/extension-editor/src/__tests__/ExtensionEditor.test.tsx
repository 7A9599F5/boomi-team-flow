/**
 * @jest-environment jsdom
 */
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ExtensionEditor } from '../ExtensionEditor';
import { IObjectDataEntry } from '../types';

// Mock ReactDOM.createPortal for ConfirmationDialog tests
jest.mock('react-dom', () => {
    const original = jest.requireActual('react-dom');
    return {
        ...original,
        createPortal: (node: React.ReactNode) => node,
    };
});

// Mock react-window to avoid layout calculation issues in JSDOM
jest.mock('react-window', () => ({
    FixedSizeList: ({ children, itemCount, itemData }: any) => {
        const rows = [];
        for (let i = 0; i < itemCount; i++) {
            rows.push(
                React.createElement(children, {
                    key: i,
                    index: i,
                    style: {},
                    data: itemData,
                }),
            );
        }
        return React.createElement('div', { 'data-testid': 'virtual-list' }, ...rows);
    },
}));

const sampleExtensionJson = JSON.stringify({
    accountId: 'ABC-PROD',
    environmentId: 'env-prod-001',
    environmentName: 'Production',
    connections: {
        'conn-1': {
            name: 'CRM Connection',
            extensionGroupId: 'grp-1',
            properties: {
                host: { name: 'Host', value: 'prod.server.com', useDefault: false, encrypted: false },
                password: { name: 'Password', value: '***', useDefault: false, encrypted: true },
            },
        },
    },
    operations: {
        'op-1': {
            name: 'Get Orders',
            extensionGroupId: 'grp-2',
            properties: {
                maxRecords: { name: 'Max Records', value: '100', useDefault: false, encrypted: false },
            },
        },
    },
    processProperties: {
        'pp-1': { name: 'BASE_URL', value: 'https://api.prod.co', useDefault: false, encrypted: false },
    },
});

const sampleAccessMappingsJson = JSON.stringify([
    {
        processId: 'proc-1',
        processName: 'Order Processing',
        extensionIds: ['conn-1', 'op-1', 'pp-1'],
        adminOnly: false,
    },
]);

function makeObjectData(
    extensionData = sampleExtensionJson,
    accessMappings = sampleAccessMappingsJson,
    isAdmin = 'false',
    ssoGroups = 'ABC_BOOMI_FLOW_CONTRIBUTOR',
): IObjectDataEntry[] {
    return [
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
}

const defaultProps = {
    id: 'test-editor',
    flowKey: 'test-flow',
    model: {
        isVisible: true,
        isEnabled: true,
        attributes: {},
        objectData: null,
        objectDataRequest: null,
        contentType: '',
        label: '',
        developerName: '',
    },
    state: { loading: false, error: null, objectData: null },
    classes: [],
};

describe('ExtensionEditor', () => {
    it('renders loading state when state.loading is true', () => {
        render(
            <ExtensionEditor
                {...defaultProps}
                state={{ loading: true, error: null, objectData: null }}
                objectData={null}
            />,
        );
        expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders error state when objectData is null', () => {
        render(<ExtensionEditor {...defaultProps} objectData={null} />);
        expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders environment selector with account and environment', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(screen.getByLabelText('Select account')).toBeInTheDocument();
        expect(screen.getByLabelText('Select environment')).toBeInTheDocument();
    });

    it('renders search bar', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(screen.getByLabelText('Search extensions')).toBeInTheDocument();
    });

    it('renders extension tree with Connections category', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(screen.getByText(/Connections/i)).toBeInTheDocument();
    });

    it('renders extension tree with Operations category', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(screen.getByText(/Operations/i)).toBeInTheDocument();
    });

    it('renders extension tree with Process Properties category', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(screen.getByText(/Process Properties/i)).toBeInTheDocument();
    });

    it('shows no-selection message when no node is selected', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(
            screen.getByText(/Select an extension from the tree/),
        ).toBeInTheDocument();
    });

    it('shows property table when a node is selected', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        // Click the Operations item
        const opItem = screen.getByText('Get Orders');
        fireEvent.click(opItem);
        // Property table should appear
        expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('shows connection banner when a connection node is selected', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        const connItem = screen.getByText('CRM Connection');
        fireEvent.click(connItem);
        // Connection banner should appear (read-only for non-admin)
        expect(screen.getByLabelText('Connection extension read-only')).toBeInTheDocument();
    });

    it('shows connection admin banner for admin users', () => {
        render(
            <ExtensionEditor
                {...defaultProps}
                objectData={makeObjectData(sampleExtensionJson, sampleAccessMappingsJson, 'true', 'ABC_BOOMI_FLOW_ADMIN')}
            />,
        );
        const connItem = screen.getByText('CRM Connection');
        fireEvent.click(connItem);
        expect(screen.getByLabelText('Connection extension admin notice')).toBeInTheDocument();
    });

    it('shows DPP banner when process property is selected', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        const ppItem = screen.getByText('BASE_URL');
        fireEvent.click(ppItem);
        expect(screen.getByLabelText('Environment-wide process property notice')).toBeInTheDocument();
    });

    it('renders save toolbar', () => {
        render(<ExtensionEditor {...defaultProps} objectData={makeObjectData()} />);
        expect(screen.getByRole('toolbar', { name: 'Extension editor actions' })).toBeInTheDocument();
    });

    it('shows unsaved changes count after edit', () => {
        render(
            <ExtensionEditor
                {...defaultProps}
                objectData={makeObjectData(sampleExtensionJson, sampleAccessMappingsJson, 'false', 'ABC_BOOMI_FLOW_CONTRIBUTOR')}
            />,
        );
        // Select an operation (editable by contributors)
        fireEvent.click(screen.getByText('Get Orders'));
        // Edit the max records field
        const editableCell = screen.getByText('100');
        fireEvent.click(editableCell);
        const input = screen.getByLabelText('Edit property value');
        fireEvent.change(input, { target: { value: '200' } });
        fireEvent.blur(input);
        // Dirty indicator should appear
        expect(screen.getByText(/1 unsaved change/)).toBeInTheDocument();
    });

    it('renders error state for invalid extension JSON', () => {
        render(
            <ExtensionEditor
                {...defaultProps}
                objectData={makeObjectData('{invalid json', sampleAccessMappingsJson)}
            />,
        );
        expect(screen.getByRole('alert')).toBeInTheDocument();
    });
});
