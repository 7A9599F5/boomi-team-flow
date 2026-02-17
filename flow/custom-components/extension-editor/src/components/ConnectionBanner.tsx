import * as React from 'react';

interface IConnectionBannerProps {
    canEdit: boolean;
}

/**
 * Admin-only indicator banner for connection extensions.
 *
 * If the user is an admin (canEdit=true): shows an informational note about
 * the admin requirement. If the user is not an admin (canEdit=false): shows
 * a read-only message directing them to contact an administrator.
 */
export const ConnectionBanner: React.FC<IConnectionBannerProps> = React.memo(
    ({ canEdit }) => {
        if (canEdit) {
            return (
                <div
                    className="ee-banner ee-banner--admin"
                    role="note"
                    aria-label="Connection extension admin notice"
                >
                    <span className="ee-banner__icon" aria-hidden="true">&#128274;</span>
                    <div className="ee-banner__body">
                        <strong className="ee-banner__title">
                            Connection extensions require Admin privileges to edit.
                        </strong>
                    </div>
                </div>
            );
        }

        return (
            <div
                className="ee-banner ee-banner--readonly"
                role="alert"
                aria-label="Connection extension read-only"
            >
                <span className="ee-banner__icon" aria-hidden="true">&#128274;</span>
                <div className="ee-banner__body">
                    <strong className="ee-banner__title">
                        Read-only — contact an administrator to modify connection settings.
                    </strong>
                </div>
            </div>
        );
    },
);

ConnectionBanner.displayName = 'ConnectionBanner';
