import * as React from 'react';

interface ISharedResourceBannerProps {
    processNames: string[];
}

/**
 * Warning banner shown when the selected extension is used by 2 or more processes.
 *
 * Informs the user that any changes will affect all listed processes.
 * Uses amber/warning styling to convey risk.
 */
export const SharedResourceBanner: React.FC<ISharedResourceBannerProps> = React.memo(
    ({ processNames }) => {
        if (processNames.length < 2) {
            return null;
        }

        return (
            <div
                className="ee-banner ee-banner--warning"
                role="alert"
                aria-label="Shared extension warning"
            >
                <span className="ee-banner__icon" aria-hidden="true">&#9888;</span>
                <div className="ee-banner__body">
                    <strong className="ee-banner__title">
                        This extension is used by {processNames.length} processes:{' '}
                        {processNames.join(', ')}
                    </strong>
                    <p className="ee-banner__message">
                        Changes will affect all processes using this extension.
                    </p>
                </div>
            </div>
        );
    },
);

SharedResourceBanner.displayName = 'SharedResourceBanner';
