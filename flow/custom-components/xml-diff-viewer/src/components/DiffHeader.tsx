import * as React from 'react';
import { IDiffData, IDiffStats } from '../types';

interface DiffHeaderProps {
    data: IDiffData;
    stats: IDiffStats;
}

/**
 * Header bar showing component name badge, action badge, version info, and change stats.
 */
export const DiffHeader: React.FC<DiffHeaderProps> = ({ data, stats }) => {
    const { componentName, componentAction, branchVersion, mainVersion } = data;
    const { additions, deletions, unchanged } = stats;

    const actionClass =
        componentAction === 'CREATE'
            ? 'xml-diff-badge--create'
            : 'xml-diff-badge--update';

    return (
        <div className="xml-diff-header">
            <div className="xml-diff-header__left">
                <span className="xml-diff-badge xml-diff-badge--name">
                    {componentName}
                </span>
                <span className={`xml-diff-badge ${actionClass}`}>
                    {componentAction}
                </span>
                {componentAction === 'UPDATE' &&
                    (mainVersion > 0 || branchVersion > 0) && (
                        <span className="xml-diff-version">
                            main v{mainVersion} &rarr; branch v{branchVersion}
                        </span>
                    )}
            </div>
            <div
                className="xml-diff-header__right xml-diff-summary"
                aria-label={`${additions} additions, ${deletions} deletions, ${unchanged} unchanged lines`}
            >
                <span className="xml-diff-stat xml-diff-stat--add">
                    +{additions}
                </span>
                <span className="xml-diff-stat xml-diff-stat--del">
                    &minus;{deletions}
                </span>
                <span className="xml-diff-stat xml-diff-stat--unchanged">
                    {unchanged} unchanged
                </span>
            </div>
        </div>
    );
};
