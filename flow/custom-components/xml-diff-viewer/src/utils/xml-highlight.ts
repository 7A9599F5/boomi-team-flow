import Prism from 'prismjs';
import 'prismjs/components/prism-markup';

/**
 * Highlight XML source code using Prism.js markup grammar.
 * Returns an HTML string suitable for dangerouslySetInnerHTML.
 *
 * Used as the `renderContent` callback for react-diff-viewer-continued.
 */
export function highlightXml(source: string): string {
    try {
        return Prism.highlight(source, Prism.languages.markup, 'markup');
    } catch {
        // Fallback: return escaped plain text if Prism fails
        return source
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }
}

/**
 * Render function compatible with react-diff-viewer-continued's renderContent prop.
 * Returns a React element with highlighted XML.
 */
export function renderHighlightedContent(source: string): JSX.Element {
    const html = highlightXml(source);
    return (
        <span
            dangerouslySetInnerHTML={{ __html: html }}
            className="xml-diff-highlighted"
        />
    );
}
