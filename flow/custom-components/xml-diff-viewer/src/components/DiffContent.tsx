import * as React from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { IToolbarState } from '../types';
import { renderHighlightedContent } from '../utils/xml-highlight';
import { lightThemeStyles } from '../utils/diff-styles';

interface DiffContentProps {
    oldValue: string;
    newValue: string;
    toolbar: IToolbarState;
}

/**
 * Wraps react-diff-viewer-continued with Prism XML syntax highlighting,
 * code folding, and theme overrides.
 */
export const DiffContent: React.FC<DiffContentProps> = ({
    oldValue,
    newValue,
    toolbar,
}) => {
    const containerClass = [
        'xml-diff-content',
        toolbar.wrapLines ? 'xml-diff-content--wrap' : '',
    ]
        .filter(Boolean)
        .join(' ');

    return (
        <div className={containerClass} role="table" aria-label="XML diff comparison">
            <ReactDiffViewer
                oldValue={oldValue}
                newValue={newValue}
                splitView={toolbar.viewMode === 'split'}
                showDiffOnly={!toolbar.expandAll}
                extraLinesSurroundingDiff={3}
                renderContent={renderHighlightedContent}
                codeFoldMessageRenderer={codeFoldMessage}
                compareMethod={DiffMethod.LINES}
                styles={lightThemeStyles}
                leftTitle="main"
                rightTitle="branch"
            />
        </div>
    );
};

/**
 * Renders the "Show N hidden lines" fold message.
 */
function codeFoldMessage(
    totalFoldedLines: number,
    _leftStartLineNumber: number,
    _rightStartLineNumber: number,
): React.ReactElement {
    return (
        <span className="xml-diff-fold-message">
            Show {totalFoldedLines} hidden lines
        </span>
    );
}
