import * as React from 'react';
import { IToolbarState, ViewMode } from '../types';
import { useClipboard } from '../hooks/useClipboard';

interface DiffToolbarProps {
    toolbar: IToolbarState;
    canToggleSplit: boolean;
    branchXml: string;
    mainXml: string;
    onViewModeChange: (mode: ViewMode) => void;
    onExpandAllChange: (expand: boolean) => void;
    onWrapLinesChange: (wrap: boolean) => void;
}

/**
 * Toolbar with view mode toggle, expand all, wrap lines, and copy buttons.
 * Split toggle is hidden on mobile breakpoints.
 */
export const DiffToolbar: React.FC<DiffToolbarProps> = ({
    toolbar,
    canToggleSplit,
    branchXml,
    mainXml,
    onViewModeChange,
    onExpandAllChange,
    onWrapLinesChange,
}) => {
    const branchClipboard = useClipboard();
    const mainClipboard = useClipboard();

    return (
        <div className="xml-diff-toolbar__controls" role="toolbar" aria-label="Diff view controls">
            {canToggleSplit && (
                <div className="xml-diff-toggle" role="radiogroup" aria-label="View mode">
                    <button
                        type="button"
                        role="radio"
                        aria-checked={toolbar.viewMode === 'split'}
                        className={`xml-diff-toggle__btn ${toolbar.viewMode === 'split' ? 'xml-diff-toggle__btn--active' : ''}`}
                        onClick={() => onViewModeChange('split')}
                    >
                        Split
                    </button>
                    <button
                        type="button"
                        role="radio"
                        aria-checked={toolbar.viewMode === 'unified'}
                        className={`xml-diff-toggle__btn ${toolbar.viewMode === 'unified' ? 'xml-diff-toggle__btn--active' : ''}`}
                        onClick={() => onViewModeChange('unified')}
                    >
                        Unified
                    </button>
                </div>
            )}

            <button
                type="button"
                className={`xml-diff-btn ${toolbar.expandAll ? 'xml-diff-btn--active' : ''}`}
                onClick={() => onExpandAllChange(!toolbar.expandAll)}
                aria-pressed={toolbar.expandAll}
                aria-label={toolbar.expandAll ? 'Collapse unchanged lines' : 'Expand all lines'}
            >
                {toolbar.expandAll ? 'Collapse' : 'Expand All'}
            </button>

            <button
                type="button"
                className={`xml-diff-btn ${toolbar.wrapLines ? 'xml-diff-btn--active' : ''}`}
                onClick={() => onWrapLinesChange(!toolbar.wrapLines)}
                aria-pressed={toolbar.wrapLines}
                aria-label={toolbar.wrapLines ? 'Disable line wrapping' : 'Enable line wrapping'}
            >
                Wrap Lines
            </button>

            <div className="xml-diff-toolbar__copy">
                <button
                    type="button"
                    className="xml-diff-btn xml-diff-btn--copy"
                    onClick={() => branchClipboard.copy(branchXml)}
                    aria-label="Copy branch XML to clipboard"
                >
                    {branchClipboard.status === 'copied'
                        ? 'Copied!'
                        : 'Copy Branch'}
                </button>
                {mainXml && (
                    <button
                        type="button"
                        className="xml-diff-btn xml-diff-btn--copy"
                        onClick={() => mainClipboard.copy(mainXml)}
                        aria-label="Copy main XML to clipboard"
                    >
                        {mainClipboard.status === 'copied'
                            ? 'Copied!'
                            : 'Copy Main'}
                    </button>
                )}
            </div>
        </div>
    );
};
