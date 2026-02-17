import { computeDiffStats } from '../hooks/useDiffStats';

describe('computeDiffStats', () => {
    it('returns zeros for empty inputs', () => {
        const stats = computeDiffStats('', '');
        expect(stats).toEqual({ additions: 0, deletions: 0, unchanged: 0 });
    });

    it('counts all lines as additions for CREATE (empty old)', () => {
        const newValue = '<root>\n  <child />\n</root>';
        const stats = computeDiffStats('', newValue);
        expect(stats.additions).toBe(3);
        expect(stats.deletions).toBe(0);
        expect(stats.unchanged).toBe(0);
    });

    it('counts all lines as deletions for empty new value', () => {
        const oldValue = '<root>\n  <child />\n</root>';
        const stats = computeDiffStats(oldValue, '');
        expect(stats.additions).toBe(0);
        expect(stats.deletions).toBe(3);
        expect(stats.unchanged).toBe(0);
    });

    it('computes correct stats for UPDATE with changes', () => {
        const oldValue = [
            '<Component>',
            '  <Name>Process</Name>',
            '  <Timeout>30</Timeout>',
            '</Component>',
        ].join('\n');

        const newValue = [
            '<Component>',
            '  <Name>Process</Name>',
            '  <Timeout>60</Timeout>',
            '  <Retry>3</Retry>',
            '</Component>',
        ].join('\n');

        const stats = computeDiffStats(oldValue, newValue);
        // <Component>, <Name>Process</Name>, </Component> are unchanged = 3
        // <Timeout>30</Timeout> deleted = 1
        // <Timeout>60</Timeout>, <Retry>3</Retry> added = 2
        expect(stats.unchanged).toBe(3);
        expect(stats.deletions).toBe(1);
        expect(stats.additions).toBe(2);
    });

    it('handles identical content with zero changes', () => {
        const content = '<root>\n  <child />\n</root>';
        const stats = computeDiffStats(content, content);
        expect(stats.additions).toBe(0);
        expect(stats.deletions).toBe(0);
        expect(stats.unchanged).toBe(3);
    });

    it('handles single-line change', () => {
        const stats = computeDiffStats('old line', 'new line');
        expect(stats.additions).toBe(1);
        expect(stats.deletions).toBe(1);
        expect(stats.unchanged).toBe(0);
    });
});
