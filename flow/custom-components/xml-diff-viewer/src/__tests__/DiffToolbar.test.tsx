/**
 * @jest-environment jsdom
 */
import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DiffToolbar } from '../components/DiffToolbar';
import { IToolbarState } from '../types';

const defaultToolbar: IToolbarState = {
    viewMode: 'split',
    expandAll: false,
    wrapLines: false,
};

const noop = () => {};

const renderToolbar = (
    overrides?: Partial<{
        toolbar: IToolbarState;
        canToggleSplit: boolean;
        branchXml: string;
        mainXml: string;
        onViewModeChange: (mode: any) => void;
        onExpandAllChange: (v: boolean) => void;
        onWrapLinesChange: (v: boolean) => void;
    }>,
) =>
    render(
        <DiffToolbar
            toolbar={overrides?.toolbar ?? defaultToolbar}
            canToggleSplit={overrides?.canToggleSplit ?? true}
            branchXml={overrides?.branchXml ?? '<branch />'}
            mainXml={overrides?.mainXml ?? '<main />'}
            onViewModeChange={overrides?.onViewModeChange ?? noop}
            onExpandAllChange={overrides?.onExpandAllChange ?? noop}
            onWrapLinesChange={overrides?.onWrapLinesChange ?? noop}
        />,
    );

describe('DiffToolbar', () => {
    it('renders split/unified toggle when canToggleSplit is true', () => {
        renderToolbar();
        expect(screen.getByText('Split')).toBeInTheDocument();
        expect(screen.getByText('Unified')).toBeInTheDocument();
    });

    it('hides split/unified toggle when canToggleSplit is false', () => {
        renderToolbar({ canToggleSplit: false });
        expect(screen.queryByText('Split')).not.toBeInTheDocument();
    });

    it('calls onViewModeChange when unified button clicked', () => {
        const onViewModeChange = jest.fn();
        renderToolbar({ onViewModeChange });
        fireEvent.click(screen.getByText('Unified'));
        expect(onViewModeChange).toHaveBeenCalledWith('unified');
    });

    it('calls onExpandAllChange when expand all button clicked', () => {
        const onExpandAllChange = jest.fn();
        renderToolbar({ onExpandAllChange });
        fireEvent.click(screen.getByText('Expand All'));
        expect(onExpandAllChange).toHaveBeenCalledWith(true);
    });

    it('shows Collapse text when expandAll is true', () => {
        renderToolbar({
            toolbar: { ...defaultToolbar, expandAll: true },
        });
        expect(screen.getByText('Collapse')).toBeInTheDocument();
    });

    it('calls onWrapLinesChange when wrap lines button clicked', () => {
        const onWrapLinesChange = jest.fn();
        renderToolbar({ onWrapLinesChange });
        fireEvent.click(screen.getByText('Wrap Lines'));
        expect(onWrapLinesChange).toHaveBeenCalledWith(true);
    });

    it('renders copy branch button', () => {
        renderToolbar();
        expect(
            screen.getByLabelText('Copy branch XML to clipboard'),
        ).toBeInTheDocument();
    });

    it('renders copy main button when mainXml is provided', () => {
        renderToolbar({ mainXml: '<main />' });
        expect(
            screen.getByLabelText('Copy main XML to clipboard'),
        ).toBeInTheDocument();
    });

    it('hides copy main button when mainXml is empty', () => {
        renderToolbar({ mainXml: '' });
        expect(
            screen.queryByLabelText('Copy main XML to clipboard'),
        ).not.toBeInTheDocument();
    });

    it('has aria-pressed on toggle buttons', () => {
        renderToolbar({
            toolbar: { ...defaultToolbar, wrapLines: true },
        });
        const wrapBtn = screen.getByText('Wrap Lines');
        expect(wrapBtn).toHaveAttribute('aria-pressed', 'true');
    });

    it('has toolbar role on controls container', () => {
        renderToolbar();
        expect(screen.getByRole('toolbar')).toBeInTheDocument();
    });
});
