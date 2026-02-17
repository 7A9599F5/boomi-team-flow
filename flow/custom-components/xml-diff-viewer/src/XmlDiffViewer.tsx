import * as React from 'react';
import { useState, useEffect } from 'react';
import { IWrappedComponentProps } from './utils/wrapper';
import { extractDiffData } from './utils/objectData';
import { IDiffData, IToolbarState, ViewMode } from './types';
import { useResponsive } from './hooks/useResponsive';
import { useDiffStats } from './hooks/useDiffStats';
import { DiffHeader } from './components/DiffHeader';
import { DiffToolbar } from './components/DiffToolbar';
import { DiffContent } from './components/DiffContent';
import { CreateView } from './components/CreateView';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';
import './styles/xml-diff-viewer.css';

/**
 * XmlDiffViewer — main orchestrator component for Boomi Flow.
 *
 * Receives objectData from Flow runtime via HOC wrapper, extracts diff data,
 * and renders the appropriate view based on component action (CREATE vs UPDATE).
 */
export const XmlDiffViewer: React.FC<IWrappedComponentProps> = ({
    objectData,
    state,
}) => {
    const { defaultViewMode, canToggleSplit } = useResponsive();

    const [toolbar, setToolbar] = useState<IToolbarState>({
        viewMode: defaultViewMode,
        expandAll: false,
        wrapLines: false,
    });

    // Update view mode when breakpoint changes
    useEffect(() => {
        setToolbar((prev) => ({
            ...prev,
            viewMode: defaultViewMode,
        }));
    }, [defaultViewMode]);

    // Show loading state when Flow is fetching data
    if (state?.loading) {
        return <LoadingState />;
    }

    // Extract and validate diff data from objectData
    const data: IDiffData | null = extractDiffData(objectData);

    if (!data) {
        return <ErrorState message="No component data available" />;
    }

    if (!data.branchXml) {
        return <ErrorState message="Branch XML data is missing" />;
    }

    // Compute diff statistics
    const stats = useDiffStats(data.mainXml, data.branchXml);

    const handleViewModeChange = (mode: ViewMode) => {
        setToolbar((prev) => ({ ...prev, viewMode: mode }));
    };

    const handleExpandAllChange = (expand: boolean) => {
        setToolbar((prev) => ({ ...prev, expandAll: expand }));
    };

    const handleWrapLinesChange = (wrap: boolean) => {
        setToolbar((prev) => ({ ...prev, wrapLines: wrap }));
    };

    const isCreate = data.componentAction === 'CREATE';

    return (
        <div className="xml-diff-viewer">
            <DiffHeader data={data} stats={stats} />
            <DiffToolbar
                toolbar={toolbar}
                canToggleSplit={canToggleSplit && !isCreate}
                branchXml={data.branchXml}
                mainXml={data.mainXml}
                onViewModeChange={handleViewModeChange}
                onExpandAllChange={handleExpandAllChange}
                onWrapLinesChange={handleWrapLinesChange}
            />
            {isCreate ? (
                <CreateView newValue={data.branchXml} toolbar={toolbar} />
            ) : (
                <DiffContent
                    oldValue={data.mainXml}
                    newValue={data.branchXml}
                    toolbar={toolbar}
                />
            )}
        </div>
    );
};
