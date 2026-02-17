/**
 * Style overrides for react-diff-viewer-continued.
 * These are passed via the `styles` prop and override the default theme.
 * Uses GitHub-style diff colors.
 */

export const lightThemeStyles = {
    variables: {
        light: {
            diffViewerBackground: '#ffffff',
            diffViewerColor: '#24292f',
            addedBackground: '#e6ffec',
            addedColor: '#24292f',
            removedBackground: '#ffebe9',
            removedColor: '#24292f',
            wordAddedBackground: '#abf2bc',
            wordRemovedBackground: '#ff818266',
            addedGutterBackground: '#ccffd8',
            removedGutterBackground: '#ffd7d5',
            gutterBackground: '#f6f8fa',
            gutterBackgroundDark: '#f0f1f3',
            highlightBackground: '#fffbdd',
            highlightGutterBackground: '#fff5b1',
            codeFoldGutterBackground: '#dbedff',
            codeFoldBackground: '#f1f8ff',
            emptyLineBackground: '#fafbfc',
            gutterColor: '#636c76',
            addedGutterColor: '#116329',
            removedGutterColor: '#82071e',
            codeFoldContentColor: '#0969da',
        },
    },
    line: {
        padding: '0 10px',
    },
    gutter: {
        minWidth: '45px',
        padding: '0 10px',
    },
    codeFoldGutter: {
        backgroundColor: '#dbedff',
    },
    codeFold: {
        backgroundColor: '#f1f8ff',
        height: '30px',
        lineHeight: '30px',
        fontSize: '12px',
    },
};

export const darkThemeStyles = {
    variables: {
        dark: {
            diffViewerBackground: '#0d1117',
            diffViewerColor: '#e6edf3',
            addedBackground: '#122117',
            addedColor: '#e6edf3',
            removedBackground: '#2d1117',
            removedColor: '#e6edf3',
            wordAddedBackground: '#033a16',
            wordRemovedBackground: '#67060c',
            addedGutterBackground: '#0d2818',
            removedGutterBackground: '#3c1117',
            gutterBackground: '#161b22',
            gutterBackgroundDark: '#1c2128',
            highlightBackground: '#3b2e00',
            highlightGutterBackground: '#5c4813',
            codeFoldGutterBackground: '#182438',
            codeFoldBackground: '#161b22',
            emptyLineBackground: '#161b22',
            gutterColor: '#8b949e',
            addedGutterColor: '#3fb950',
            removedGutterColor: '#f85149',
            codeFoldContentColor: '#58a6ff',
        },
    },
    line: {
        padding: '0 10px',
    },
    gutter: {
        minWidth: '45px',
        padding: '0 10px',
    },
    codeFold: {
        height: '30px',
        lineHeight: '30px',
        fontSize: '12px',
    },
};
