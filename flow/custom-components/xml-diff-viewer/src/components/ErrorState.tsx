import * as React from 'react';

interface ErrorStateProps {
    message: string;
    onRetry?: () => void;
}

/**
 * Error display with optional retry button.
 * Used when objectData is missing, branchXml is empty, or API call fails.
 */
export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => (
    <div className="xml-diff-viewer xml-diff-error" role="alert">
        <div className="xml-diff-error__icon" aria-hidden="true">
            !
        </div>
        <p className="xml-diff-error__message">{message}</p>
        {onRetry && (
            <button
                className="xml-diff-error__retry"
                onClick={onRetry}
                type="button"
            >
                Retry
            </button>
        )}
    </div>
);
