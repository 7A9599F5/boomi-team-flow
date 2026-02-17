import * as React from 'react';
import { useState, useCallback } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import { IExtensionProperty, IFieldEdit } from '../types';

interface IPropertyRow {
    propertyKey: string;
    property: IExtensionProperty;
    edit: IFieldEdit | undefined;
    canEdit: boolean;
}

interface IPropertyTableProps {
    extensionId: string;
    properties: Record<string, IExtensionProperty>;
    editedFields: Record<string, IFieldEdit>;
    canEdit: boolean;
    onSetValue: (extensionId: string, propertyKey: string, value: string) => void;
    onToggleDefault: (extensionId: string, propertyKey: string, useDefault: boolean) => void;
}

const ROW_HEIGHT = 48;
const MAX_VISIBLE_ROWS = 10;

interface IInlineEditCellProps {
    value: string;
    isEncrypted: boolean;
    canEdit: boolean;
    onChange: (value: string) => void;
}

/**
 * Inline editable cell — click to enter edit mode.
 */
const InlineEditCell: React.FC<IInlineEditCellProps> = React.memo(
    ({ value, isEncrypted, canEdit, onChange }) => {
        const [isEditing, setIsEditing] = useState(false);
        const [localValue, setLocalValue] = useState(value);

        const handleClick = useCallback(() => {
            if (canEdit && !isEncrypted) {
                setLocalValue(value);
                setIsEditing(true);
            }
        }, [canEdit, isEncrypted, value]);

        const handleBlur = useCallback(() => {
            setIsEditing(false);
            if (localValue !== value) {
                onChange(localValue);
            }
        }, [localValue, value, onChange]);

        const handleKeyDown = useCallback(
            (e: React.KeyboardEvent<HTMLInputElement>) => {
                if (e.key === 'Enter') {
                    setIsEditing(false);
                    if (localValue !== value) {
                        onChange(localValue);
                    }
                } else if (e.key === 'Escape') {
                    setIsEditing(false);
                    setLocalValue(value);
                }
            },
            [localValue, value, onChange],
        );

        if (isEncrypted) {
            return (
                <span className="ee-table__cell-value ee-table__cell-value--encrypted">
                    <span className="ee-table__encrypted-mask" aria-label="Encrypted value">
                        &#9679;&#9679;&#9679;&#9679;&#9679;&#9679;
                    </span>
                    <span className="ee-table__encrypted-badge">encrypted</span>
                </span>
            );
        }

        if (isEditing) {
            return (
                <input
                    type="text"
                    className="ee-table__cell-input"
                    value={localValue}
                    onChange={(e) => setLocalValue(e.target.value)}
                    onBlur={handleBlur}
                    onKeyDown={handleKeyDown}
                    autoFocus
                    aria-label="Edit property value"
                />
            );
        }

        return (
            <span
                className={`ee-table__cell-value${canEdit ? ' ee-table__cell-value--editable' : ''}`}
                onClick={handleClick}
                role={canEdit ? 'button' : undefined}
                tabIndex={canEdit ? 0 : undefined}
                onKeyDown={canEdit ? (e) => { if (e.key === 'Enter' || e.key === ' ') handleClick(); } : undefined}
                title={canEdit && !isEncrypted ? 'Click to edit' : undefined}
                aria-label={canEdit ? `Edit ${value || '(empty)'}` : `Value: ${value || '(empty)'}`}
            >
                {value || <em className="ee-table__empty-value">(empty)</em>}
            </span>
        );
    },
);

InlineEditCell.displayName = 'InlineEditCell';

/**
 * A single row in the property table — rendered inside react-window's FixedSizeList.
 */
interface IPropertyRowData {
    rows: IPropertyRow[];
    extensionId: string;
    onSetValue: (extensionId: string, propertyKey: string, value: string) => void;
    onToggleDefault: (extensionId: string, propertyKey: string, useDefault: boolean) => void;
}

const PropertyRow: React.FC<ListChildComponentProps<IPropertyRowData>> = ({
    index,
    style,
    data,
}) => {
    const { rows, extensionId, onSetValue, onToggleDefault } = data;
    const row = rows[index];
    if (!row) return null;

    const currentValue = row.edit?.value ?? row.property.value;
    const useDefault = row.edit?.useDefault ?? row.property.useDefault;

    const handleValueChange = useCallback(
        (value: string) => {
            onSetValue(extensionId, row.propertyKey, value);
        },
        [extensionId, row.propertyKey, onSetValue],
    );

    const handleToggleDefault = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            onToggleDefault(extensionId, row.propertyKey, e.target.checked);
        },
        [extensionId, row.propertyKey, onToggleDefault],
    );

    const isDirty = row.edit !== undefined;

    return (
        <div
            style={style}
            className={`ee-table__row${isDirty ? ' ee-table__row--dirty' : ''}`}
            role="row"
        >
            <div className="ee-table__cell ee-table__cell--name" role="cell">
                <span className="ee-table__property-name">{row.property.name}</span>
                <span className="ee-table__property-key">{row.propertyKey}</span>
            </div>

            <div className="ee-table__cell ee-table__cell--value" role="cell">
                <InlineEditCell
                    value={currentValue}
                    isEncrypted={row.property.encrypted}
                    canEdit={row.canEdit}
                    onChange={handleValueChange}
                />
            </div>

            <div className="ee-table__cell ee-table__cell--default" role="cell">
                <label className="ee-table__default-label">
                    <input
                        type="checkbox"
                        checked={useDefault}
                        onChange={handleToggleDefault}
                        disabled={!row.canEdit || row.property.encrypted}
                        aria-label={`Use default value for ${row.property.name}`}
                    />
                    <span>Default</span>
                </label>
            </div>

            <div className="ee-table__cell ee-table__cell--actions" role="cell">
                {isDirty && (
                    <span
                        className="ee-table__dirty-badge"
                        aria-label="Unsaved change"
                        title="Unsaved change"
                    >
                        &#9679;
                    </span>
                )}
            </div>
        </div>
    );
};

/**
 * Inline-editable property table (right panel).
 *
 * Columns: Property Name | Current Value | Default? | Actions
 * Uses react-window (FixedSizeList) for virtual scrolling on large property lists.
 * Handles inline editing, Use Default checkbox, encrypted field masking, and
 * read-only mode for unauthorized properties.
 */
export const PropertyTable: React.FC<IPropertyTableProps> = React.memo(
    ({
        extensionId,
        properties,
        editedFields,
        canEdit,
        onSetValue,
        onToggleDefault,
    }) => {
        const rows: IPropertyRow[] = Object.entries(properties).map(
            ([key, prop]) => ({
                propertyKey: key,
                property: prop,
                edit: editedFields[`${extensionId}::${key}`],
                canEdit,
            }),
        );

        const listHeight = Math.min(rows.length, MAX_VISIBLE_ROWS) * ROW_HEIGHT;

        const itemData: IPropertyRowData = {
            rows,
            extensionId,
            onSetValue,
            onToggleDefault,
        };

        if (rows.length === 0) {
            return (
                <div className="ee-table__empty-state">
                    <p>No properties found for this extension.</p>
                </div>
            );
        }

        return (
            <div className="ee-table" role="table" aria-label="Extension properties">
                {/* Header */}
                <div className="ee-table__header" role="row">
                    <div className="ee-table__th ee-table__cell--name" role="columnheader">
                        Property Name
                    </div>
                    <div className="ee-table__th ee-table__cell--value" role="columnheader">
                        Current Value
                    </div>
                    <div className="ee-table__th ee-table__cell--default" role="columnheader">
                        Default?
                    </div>
                    <div className="ee-table__th ee-table__cell--actions" role="columnheader">
                        Status
                    </div>
                </div>

                {/* Virtual scrolling body */}
                <List
                    height={listHeight}
                    itemCount={rows.length}
                    itemSize={ROW_HEIGHT}
                    width="100%"
                    itemData={itemData}
                    className="ee-table__body"
                >
                    {PropertyRow}
                </List>
            </div>
        );
    },
);

PropertyTable.displayName = 'PropertyTable';
