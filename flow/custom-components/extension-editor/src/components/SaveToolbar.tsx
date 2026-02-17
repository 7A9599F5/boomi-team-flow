import * as React from 'react';

interface ISaveToolbarProps {
    dirtyFieldCount: number;
    canUndo: boolean;
    canRedo: boolean;
    canSave: boolean;
    hasTestEnvironment: boolean;
    onSave: () => void;
    onUndo: () => void;
    onRedo: () => void;
    onCopyTestToProd: () => void;
}

/**
 * Save/Undo/Redo/Copy toolbar at the bottom of the extension editor.
 *
 * - Save: writes serialized JSON to the Flow value, triggers "Save" outcome.
 * - Undo: reverts to previous edit snapshot (from useExtensionState).
 * - Redo: reapplies undone changes.
 * - Copy Test to Prod: triggers "CopyTestToProd" outcome (navigates to Page 11).
 * - Dirty indicator: shows unsaved change count.
 * - Buttons disabled when no changes or unauthorized.
 */
export const SaveToolbar: React.FC<ISaveToolbarProps> = React.memo(
    ({
        dirtyFieldCount,
        canUndo,
        canRedo,
        canSave,
        hasTestEnvironment,
        onSave,
        onUndo,
        onRedo,
        onCopyTestToProd,
    }) => {
        const isDirty = dirtyFieldCount > 0;

        return (
            <div
                className="ee-save-toolbar"
                role="toolbar"
                aria-label="Extension editor actions"
            >
                <div className="ee-save-toolbar__left">
                    {isDirty ? (
                        <span
                            className="ee-save-toolbar__dirty-indicator"
                            aria-live="polite"
                            aria-label={`${dirtyFieldCount} unsaved change${dirtyFieldCount !== 1 ? 's' : ''}`}
                        >
                            {dirtyFieldCount} unsaved change{dirtyFieldCount !== 1 ? 's' : ''}
                        </span>
                    ) : (
                        <span className="ee-save-toolbar__clean-indicator">
                            No unsaved changes
                        </span>
                    )}
                </div>

                <div className="ee-save-toolbar__actions">
                    <button
                        type="button"
                        className="ee-btn ee-btn--icon"
                        onClick={onUndo}
                        disabled={!canUndo}
                        aria-label="Undo last change"
                        title="Undo"
                    >
                        &#8630; Undo
                    </button>

                    <button
                        type="button"
                        className="ee-btn ee-btn--icon"
                        onClick={onRedo}
                        disabled={!canRedo}
                        aria-label="Redo last undone change"
                        title="Redo"
                    >
                        Redo &#8631;
                    </button>

                    {hasTestEnvironment && (
                        <button
                            type="button"
                            className="ee-btn ee-btn--secondary"
                            onClick={onCopyTestToProd}
                            aria-label="Copy test environment settings to production"
                        >
                            Copy Test &#8594; Prod
                        </button>
                    )}

                    <button
                        type="button"
                        className="ee-btn ee-btn--primary"
                        onClick={onSave}
                        disabled={!canSave || !isDirty}
                        aria-label={
                            !isDirty
                                ? 'No changes to save'
                                : `Save ${dirtyFieldCount} change${dirtyFieldCount !== 1 ? 's' : ''}`
                        }
                    >
                        Save
                        {isDirty && (
                            <span className="ee-save-toolbar__count">
                                {' '}({dirtyFieldCount})
                            </span>
                        )}
                    </button>
                </div>
            </div>
        );
    },
);

SaveToolbar.displayName = 'SaveToolbar';
