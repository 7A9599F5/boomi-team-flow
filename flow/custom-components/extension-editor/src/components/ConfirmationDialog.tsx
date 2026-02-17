import * as React from 'react';
import * as ReactDOM from 'react-dom';

interface IConfirmationDialogProps {
    isOpen: boolean;
    affectedProcesses: string[];
    onConfirm: () => void;
    onCancel: () => void;
}

/**
 * Confirmation modal for saving changes to a shared extension.
 *
 * Shown when the user attempts to save edits to an extension used by
 * 2 or more processes. Lists all affected processes and requires explicit
 * confirmation before proceeding.
 *
 * Uses ReactDOM.createPortal to render at document.body for proper overlay.
 */
export const ConfirmationDialog: React.FC<IConfirmationDialogProps> = React.memo(
    ({ isOpen, affectedProcesses, onConfirm, onCancel }) => {
        if (!isOpen) return null;

        const dialog = (
            <div
                className="ee-dialog-overlay"
                role="presentation"
                onClick={onCancel}
            >
                <div
                    className="ee-dialog"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="ee-dialog-title"
                    aria-describedby="ee-dialog-desc"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="ee-dialog__header">
                        <h2 id="ee-dialog-title" className="ee-dialog__title">
                            Confirm Save
                        </h2>
                    </div>

                    <div className="ee-dialog__body">
                        <p id="ee-dialog-desc" className="ee-dialog__message">
                            Are you sure? This will affect{' '}
                            <strong>{affectedProcesses.length} processes</strong>:
                        </p>
                        <ul className="ee-dialog__process-list">
                            {affectedProcesses.map((name) => (
                                <li key={name} className="ee-dialog__process-item">
                                    {name}
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="ee-dialog__footer">
                        <button
                            type="button"
                            className="ee-btn ee-btn--secondary"
                            onClick={onCancel}
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            className="ee-btn ee-btn--danger"
                            onClick={onConfirm}
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        );

        return ReactDOM.createPortal(dialog, document.body);
    },
);

ConfirmationDialog.displayName = 'ConfirmationDialog';
