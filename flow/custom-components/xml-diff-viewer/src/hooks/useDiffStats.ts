import { useMemo } from 'react';
import { IDiffStats } from '../types';

/**
 * Compute line-level diff statistics between two strings.
 * Uses a simple line-by-line comparison (matching the diff library's output).
 */
export function useDiffStats(oldValue: string, newValue: string): IDiffStats {
    return useMemo(() => {
        return computeDiffStats(oldValue, newValue);
    }, [oldValue, newValue]);
}

/**
 * Pure function to compute diff statistics.
 * Compares lines from old and new values to count additions, deletions, unchanged.
 */
export function computeDiffStats(
    oldValue: string,
    newValue: string,
): IDiffStats {
    if (!oldValue && !newValue) {
        return { additions: 0, deletions: 0, unchanged: 0 };
    }

    // For CREATE (no old value), all new lines are additions
    if (!oldValue) {
        const lines = newValue.split('\n').length;
        return { additions: lines, deletions: 0, unchanged: 0 };
    }

    // For empty new value (shouldn't happen, but guard)
    if (!newValue) {
        const lines = oldValue.split('\n').length;
        return { additions: 0, deletions: lines, unchanged: 0 };
    }

    const oldLines = oldValue.split('\n');
    const newLines = newValue.split('\n');

    // Use LCS-based approach for accurate stats
    const lcs = longestCommonSubsequence(oldLines, newLines);

    return {
        additions: newLines.length - lcs,
        deletions: oldLines.length - lcs,
        unchanged: lcs,
    };
}

/**
 * Compute length of longest common subsequence between two string arrays.
 * O(n*m) dynamic programming approach.
 */
function longestCommonSubsequence(a: string[], b: string[]): number {
    const m = a.length;
    const n = b.length;

    // Use 1D DP array (space-optimized)
    const prev = new Array(n + 1).fill(0);
    const curr = new Array(n + 1).fill(0);

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (a[i - 1] === b[j - 1]) {
                curr[j] = prev[j - 1] + 1;
            } else {
                curr[j] = Math.max(prev[j], curr[j - 1]);
            }
        }
        // Copy curr to prev
        for (let j = 0; j <= n; j++) {
            prev[j] = curr[j];
            curr[j] = 0;
        }
    }

    return prev[n];
}
