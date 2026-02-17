import * as React from 'react';
import ReactDiffViewer from 'react-diff-viewer-continued';
import { IToolbarState } from '../types';
import { renderHighlightedContent } from '../utils/xml-highlight';
import { lightThemeStyles } from '../utils/diff-styles';

interface CreateViewProps {
    newValue: string;
    toolbar: IToolbarState;
}

/**
 * Single-pane "all new" view for CREATE actions.
 * Renders with oldValue="" so all lines appear as additions (green).
 */
export const CreateView: React.FC<CreateViewProps> = ({
    newValue,
    toolbar,
}) => {
    const containerClass = [
        'xml-diff-content',
        'xml-diff-content--create',
        toolbar.wrapLines ? 'xml-diff-content--wrap' : '',
    ]
        .filter(Boolean)
        .join(' ');

    return (
        <div className={containerClass} role="table" aria-label="New component XML">
            <ReactDiffViewer
                oldValue=""
                newValue={newValue}
                splitView={false}
                showDiffOnly={false}
                renderContent={renderHighlightedContent}
                styles={lightThemeStyles}
                rightTitle="branch (new)"
            />
        </div>
    );
};
