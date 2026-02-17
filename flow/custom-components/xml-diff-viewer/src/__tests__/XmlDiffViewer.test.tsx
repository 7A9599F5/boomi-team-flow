/**
 * @jest-environment jsdom
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { XmlDiffViewer } from '../XmlDiffViewer';
import { IObjectDataEntry } from '../types';

// Mock react-diff-viewer-continued to avoid complex DOM rendering in tests
jest.mock('react-diff-viewer-continued', () => {
    const MockDiffViewer = (props: any) => (
        <div data-testid="mock-diff-viewer">
            <span data-testid="split-view">
                {String(props.splitView)}
            </span>
            <span data-testid="old-value">{props.oldValue}</span>
            <span data-testid="new-value">{props.newValue}</span>
        </div>
    );
    MockDiffViewer.default = MockDiffViewer;
    return {
        __esModule: true,
        default: MockDiffViewer,
        DiffMethod: { LINES: 'diffLines' },
    };
});

// Mock Prism to avoid loading in JSDOM
jest.mock('prismjs', () => ({
    highlight: (code: string) => code,
    languages: { markup: {} },
}));
jest.mock('prismjs/components/prism-markup', () => {});

const makeObjectData = (
    overrides?: Partial<Record<string, string>>,
): IObjectDataEntry[] => {
    const defaults: Record<string, string> = {
        branchXml: '<Component version="4"><Name>Order</Name></Component>',
        mainXml: '<Component version="3"><Name>Order</Name></Component>',
        componentName: 'OrderProcess',
        componentAction: 'UPDATE',
        branchVersion: '4',
        mainVersion: '3',
        ...overrides,
    };

    return [
        {
            internalId: 'test-1',
            externalId: 'ext-1',
            developerName: 'ComponentDiffData',
            properties: Object.entries(defaults).map(([name, value]) => ({
                developerName: name,
                contentValue: value,
                contentType: 'ContentString',
                objectData: null,
            })),
        },
    ];
};

const defaultProps = {
    id: 'test-id',
    flowKey: 'test-flow',
    model: { isVisible: true, isEnabled: true, attributes: {}, objectData: null, objectDataRequest: null, contentType: '', label: '', developerName: '' },
    state: { loading: false, error: null, objectData: null },
    classes: [],
};

describe('XmlDiffViewer', () => {
    it('renders loading state when state.loading is true', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                state={{ loading: true, error: null, objectData: null }}
                objectData={null}
            />,
        );
        expect(screen.getByRole('status')).toBeInTheDocument();
        expect(screen.getByText('Loading component diff...')).toBeInTheDocument();
    });

    it('renders error state when objectData is null', () => {
        render(
            <XmlDiffViewer {...defaultProps} objectData={null} />,
        );
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText('No component data available')).toBeInTheDocument();
    });

    it('renders error state when objectData is empty array', () => {
        render(
            <XmlDiffViewer {...defaultProps} objectData={[]} />,
        );
        expect(screen.getByText('No component data available')).toBeInTheDocument();
    });

    it('renders error state when branchXml is missing', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                objectData={makeObjectData({ branchXml: '' })}
            />,
        );
        expect(screen.getByText('No component data available')).toBeInTheDocument();
    });

    it('renders diff viewer for UPDATE action', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                objectData={makeObjectData()}
            />,
        );
        expect(screen.getByText('OrderProcess')).toBeInTheDocument();
        expect(screen.getByText('UPDATE')).toBeInTheDocument();
        expect(screen.getByTestId('mock-diff-viewer')).toBeInTheDocument();
    });

    it('renders component name and action badge', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                objectData={makeObjectData()}
            />,
        );
        expect(screen.getByText('OrderProcess')).toBeInTheDocument();
        expect(screen.getByText('UPDATE')).toBeInTheDocument();
    });

    it('renders CREATE view for CREATE action', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                objectData={makeObjectData({
                    componentAction: 'CREATE',
                    mainXml: '',
                    mainVersion: '0',
                })}
            />,
        );
        expect(screen.getByText('CREATE')).toBeInTheDocument();
        const diffViewer = screen.getByTestId('mock-diff-viewer');
        expect(diffViewer.querySelector('[data-testid="old-value"]')?.textContent).toBe('');
    });

    it('displays version info for UPDATE', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                objectData={makeObjectData()}
            />,
        );
        expect(screen.getByText(/main v3/)).toBeInTheDocument();
    });

    it('renders toolbar with controls', () => {
        render(
            <XmlDiffViewer
                {...defaultProps}
                objectData={makeObjectData()}
            />,
        );
        expect(screen.getByRole('toolbar')).toBeInTheDocument();
        expect(screen.getByText('Expand All')).toBeInTheDocument();
        expect(screen.getByText('Wrap Lines')).toBeInTheDocument();
    });
});
