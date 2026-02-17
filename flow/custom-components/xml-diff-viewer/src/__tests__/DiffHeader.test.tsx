/**
 * @jest-environment jsdom
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DiffHeader } from '../components/DiffHeader';
import { IDiffData, IDiffStats } from '../types';

const makeData = (overrides?: Partial<IDiffData>): IDiffData => ({
    branchXml: '<Component />',
    mainXml: '<Component />',
    componentName: 'OrderProcess',
    componentAction: 'UPDATE',
    branchVersion: 4,
    mainVersion: 3,
    ...overrides,
});

const makeStats = (overrides?: Partial<IDiffStats>): IDiffStats => ({
    additions: 12,
    deletions: 3,
    unchanged: 45,
    ...overrides,
});

describe('DiffHeader', () => {
    it('displays component name', () => {
        render(<DiffHeader data={makeData()} stats={makeStats()} />);
        expect(screen.getByText('OrderProcess')).toBeInTheDocument();
    });

    it('shows UPDATE badge for update action', () => {
        render(<DiffHeader data={makeData()} stats={makeStats()} />);
        expect(screen.getByText('UPDATE')).toBeInTheDocument();
    });

    it('shows CREATE badge for create action', () => {
        render(
            <DiffHeader
                data={makeData({ componentAction: 'CREATE' })}
                stats={makeStats()}
            />,
        );
        expect(screen.getByText('CREATE')).toBeInTheDocument();
    });

    it('displays version info for UPDATE', () => {
        render(<DiffHeader data={makeData()} stats={makeStats()} />);
        const versionEl = screen.getByText(/main v3/);
        expect(versionEl).toBeInTheDocument();
        expect(versionEl.textContent).toContain('branch v4');
    });

    it('hides version info for CREATE', () => {
        render(
            <DiffHeader
                data={makeData({ componentAction: 'CREATE' })}
                stats={makeStats()}
            />,
        );
        expect(screen.queryByText(/main v/)).not.toBeInTheDocument();
    });

    it('displays diff statistics', () => {
        render(<DiffHeader data={makeData()} stats={makeStats()} />);
        expect(screen.getByText('+12')).toBeInTheDocument();
        expect(screen.getByText('45 unchanged')).toBeInTheDocument();
        // Verify the summary container has all stats via aria-label
        const summary = screen.getByLabelText(
            '12 additions, 3 deletions, 45 unchanged lines',
        );
        expect(summary).toBeInTheDocument();
    });

    it('has accessible summary aria-label', () => {
        render(<DiffHeader data={makeData()} stats={makeStats()} />);
        const summary = screen.getByLabelText(
            '12 additions, 3 deletions, 45 unchanged lines',
        );
        expect(summary).toBeInTheDocument();
    });
});
