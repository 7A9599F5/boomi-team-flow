import * as React from 'react';

/**
 * Skeleton shimmer loading state displayed while generateComponentDiff is in progress.
 */
export const LoadingState: React.FC = () => (
    <div className="xml-diff-viewer xml-diff-loading" role="status">
        <div className="xml-diff-toolbar">
            <div className="xml-diff-skeleton xml-diff-skeleton--title" />
            <div className="xml-diff-skeleton xml-diff-skeleton--controls" />
        </div>
        <div className="xml-diff-content">
            {Array.from({ length: 8 }, (_, i) => (
                <div
                    key={i}
                    className="xml-diff-skeleton xml-diff-skeleton--line"
                    style={{ width: `${60 + Math.random() * 30}%` }}
                />
            ))}
        </div>
        <span className="xml-diff-sr-only">Loading component diff...</span>
    </div>
);
