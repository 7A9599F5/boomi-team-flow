import * as React from 'react';

/**
 * Informational banner for Dynamic Process Properties (environment-wide).
 *
 * Shown when the selected extension category is processProperties and
 * no specific per-process mapping exists for the selected property.
 * Uses info/blue styling to indicate informational nature.
 */
export const DppBanner: React.FC = React.memo(() => {
    return (
        <div
            className="ee-banner ee-banner--info"
            role="note"
            aria-label="Environment-wide process property notice"
        >
            <span className="ee-banner__icon" aria-hidden="true">&#8505;</span>
            <div className="ee-banner__body">
                <strong className="ee-banner__title">
                    Environment-wide process property
                </strong>
                <p className="ee-banner__message">
                    This is an environment-wide process property. Changes apply to all
                    processes in this environment.
                </p>
            </div>
        </div>
    );
});

DppBanner.displayName = 'DppBanner';
