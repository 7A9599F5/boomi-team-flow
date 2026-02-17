import * as React from 'react';
import { useState, useCallback, useMemo } from 'react';
import { IExtensionModel, IAccessMapping, ExtensionCategory } from '../types';

interface IExtensionTreeProps {
    extensionData: IExtensionModel;
    accessMappings: IAccessMapping[];
    selectedNodeId: string | null;
    searchQuery: string;
    isAdmin: boolean;
    onSelectNode: (nodeId: string) => void;
}

interface ITreeCategoryNode {
    id: string;
    label: string;
    category: ExtensionCategory;
    items: ITreeItemNode[];
}

interface ITreeItemNode {
    id: string;
    extensionId: string;
    label: string;
    category: ExtensionCategory;
    isShared: boolean;
    sharedByProcesses: string[];
    isConnectionExtension: boolean;
    isDppExtension: boolean;
    isAdminOnly: boolean;
}

const CATEGORY_LABELS: Record<ExtensionCategory, string> = {
    connections: 'Connections',
    operations: 'Operations',
    processProperties: 'Process Properties',
    crossReferenceOverrides: 'Cross-Reference Overrides',
};

/**
 * Check if a query string fuzzy-matches a target.
 * Case-insensitive substring match.
 */
function matchesSearch(target: string, query: string): boolean {
    if (!query) return true;
    return target.toLowerCase().includes(query.toLowerCase());
}

/**
 * Process-centric tree navigation panel (left panel).
 *
 * Groups extensions by category: connections, operations, processProperties,
 * crossReferenceOverrides. Tree nodes can be expanded/collapsed.
 * Visual indicators: lock icon for connections (admin-only), shared icon for
 * multi-process extensions. Filtered in real-time by searchQuery.
 */
export const ExtensionTree: React.FC<IExtensionTreeProps> = React.memo(
    ({
        extensionData,
        accessMappings,
        selectedNodeId,
        searchQuery,
        isAdmin,
        onSelectNode,
    }) => {
        const [expandedCategories, setExpandedCategories] = useState<Set<ExtensionCategory>>(
            () => new Set(['connections', 'operations', 'processProperties']),
        );

        // Build a map of extensionId -> processes that use it
        const extensionToProcesses = useMemo<Map<string, string[]>>(() => {
            const map = new Map<string, string[]>();
            for (const mapping of accessMappings) {
                for (const extId of mapping.extensionIds) {
                    const existing = map.get(extId) ?? [];
                    existing.push(mapping.processName);
                    map.set(extId, existing);
                }
            }
            return map;
        }, [accessMappings]);

        // Build a set of adminOnly extension IDs
        const adminOnlyExtensionIds = useMemo<Set<string>>(() => {
            const s = new Set<string>();
            for (const mapping of accessMappings) {
                if (mapping.adminOnly) {
                    for (const extId of mapping.extensionIds) {
                        s.add(extId);
                    }
                }
            }
            return s;
        }, [accessMappings]);

        // Build category nodes from extensionData
        const categoryNodes = useMemo<ITreeCategoryNode[]>(() => {
            const categories: ExtensionCategory[] = [
                'connections',
                'operations',
                'processProperties',
            ];
            if (extensionData.crossReferenceOverrides) {
                categories.push('crossReferenceOverrides');
            }

            return categories.map((category) => {
                let items: ITreeItemNode[] = [];

                if (category === 'connections') {
                    items = Object.entries(extensionData.connections).map(([id, group]) => ({
                        id: `${category}::${id}`,
                        extensionId: id,
                        label: group.name || id,
                        category,
                        isShared: (extensionToProcesses.get(id)?.length ?? 0) > 1,
                        sharedByProcesses: extensionToProcesses.get(id) ?? [],
                        isConnectionExtension: true,
                        isDppExtension: false,
                        isAdminOnly: adminOnlyExtensionIds.has(id),
                    }));
                } else if (category === 'operations') {
                    items = Object.entries(extensionData.operations).map(([id, group]) => ({
                        id: `${category}::${id}`,
                        extensionId: id,
                        label: group.name || id,
                        category,
                        isShared: (extensionToProcesses.get(id)?.length ?? 0) > 1,
                        sharedByProcesses: extensionToProcesses.get(id) ?? [],
                        isConnectionExtension: false,
                        isDppExtension: false,
                        isAdminOnly: adminOnlyExtensionIds.has(id),
                    }));
                } else if (category === 'processProperties') {
                    items = Object.entries(extensionData.processProperties).map(([id, prop]) => ({
                        id: `${category}::${id}`,
                        extensionId: id,
                        label: prop.name || id,
                        category,
                        isShared: false,
                        sharedByProcesses: [],
                        isConnectionExtension: false,
                        isDppExtension: true,
                        isAdminOnly: false,
                    }));
                } else if (category === 'crossReferenceOverrides') {
                    const overrides = extensionData.crossReferenceOverrides ?? {};
                    items = Object.entries(overrides).map(([id]) => ({
                        id: `${category}::${id}`,
                        extensionId: id,
                        label: id,
                        category,
                        isShared: false,
                        sharedByProcesses: [],
                        isConnectionExtension: false,
                        isDppExtension: false,
                        isAdminOnly: false,
                    }));
                }

                // Apply search filter
                const filteredItems = searchQuery
                    ? items.filter((item) => matchesSearch(item.label, searchQuery))
                    : items;

                return {
                    id: category,
                    label: CATEGORY_LABELS[category],
                    category,
                    items: filteredItems,
                };
            }).filter((cat) => !searchQuery || cat.items.length > 0);
        }, [extensionData, extensionToProcesses, adminOnlyExtensionIds, searchQuery]);

        const toggleCategory = useCallback((category: ExtensionCategory) => {
            setExpandedCategories((prev) => {
                const next = new Set(prev);
                if (next.has(category)) {
                    next.delete(category);
                } else {
                    next.add(category);
                }
                return next;
            });
        }, []);

        const handleItemClick = useCallback(
            (nodeId: string) => {
                onSelectNode(nodeId);
            },
            [onSelectNode],
        );

        return (
            <nav className="ee-tree" aria-label="Extension categories">
                {categoryNodes.map((catNode) => {
                    const isExpanded = expandedCategories.has(catNode.category);
                    return (
                        <div key={catNode.id} className="ee-tree__category">
                            <button
                                type="button"
                                className="ee-tree__category-header"
                                onClick={() => toggleCategory(catNode.category)}
                                aria-expanded={isExpanded}
                                aria-controls={`ee-tree-list-${catNode.id}`}
                            >
                                <span
                                    className={`ee-tree__expand-icon${isExpanded ? ' ee-tree__expand-icon--open' : ''}`}
                                    aria-hidden="true"
                                >
                                    &#9660;
                                </span>
                                <span className="ee-tree__category-label">
                                    {catNode.label}
                                </span>
                                <span className="ee-tree__count">
                                    ({catNode.items.length})
                                </span>
                            </button>

                            {isExpanded && (
                                <ul
                                    id={`ee-tree-list-${catNode.id}`}
                                    className="ee-tree__list"
                                    role="listbox"
                                    aria-label={catNode.label}
                                >
                                    {catNode.items.map((item) => (
                                        <li key={item.id} role="option" aria-selected={selectedNodeId === item.id}>
                                            <button
                                                type="button"
                                                className={`ee-tree__item${selectedNodeId === item.id ? ' ee-tree__item--selected' : ''}${item.isAdminOnly && !isAdmin ? ' ee-tree__item--locked' : ''}`}
                                                onClick={() => handleItemClick(item.id)}
                                                title={item.label}
                                            >
                                                {item.isConnectionExtension && (
                                                    <span
                                                        className="ee-tree__item-icon ee-tree__item-icon--lock"
                                                        aria-label="Admin-only connection"
                                                        title="Admin-only connection"
                                                    >
                                                        &#128274;
                                                    </span>
                                                )}
                                                {item.isShared && (
                                                    <span
                                                        className="ee-tree__item-icon ee-tree__item-icon--shared"
                                                        aria-label={`Shared by ${item.sharedByProcesses.length} processes`}
                                                        title={`Shared by: ${item.sharedByProcesses.join(', ')}`}
                                                    >
                                                        &#128257;
                                                    </span>
                                                )}
                                                <span className="ee-tree__item-label">
                                                    {item.label}
                                                </span>
                                            </button>
                                        </li>
                                    ))}
                                    {catNode.items.length === 0 && (
                                        <li className="ee-tree__empty">
                                            No matches
                                        </li>
                                    )}
                                </ul>
                            )}
                        </div>
                    );
                })}

                {categoryNodes.length === 0 && (
                    <p className="ee-tree__no-results">
                        No extensions match your search.
                    </p>
                )}
            </nav>
        );
    },
);

ExtensionTree.displayName = 'ExtensionTree';
