import { useState, useCallback } from 'react';

type CopyStatus = 'idle' | 'copied' | 'error';

/**
 * Hook for copying text to clipboard with visual feedback.
 * Uses navigator.clipboard API with execCommand fallback.
 *
 * Returns `copy` function and current status.
 * Status resets to 'idle' after 2 seconds.
 */
export function useClipboard(): {
    copy: (text: string) => void;
    status: CopyStatus;
} {
    const [status, setStatus] = useState<CopyStatus>('idle');

    const copy = useCallback((text: string) => {
        const onSuccess = () => {
            setStatus('copied');
            setTimeout(() => setStatus('idle'), 2000);
        };

        const onError = () => {
            setStatus('error');
            setTimeout(() => setStatus('idle'), 2000);
        };

        if (navigator.clipboard?.writeText) {
            navigator.clipboard.writeText(text).then(onSuccess, onError);
        } else {
            // Fallback for older browsers
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                onSuccess();
            } catch {
                onError();
            }
        }
    }, []);

    return { copy, status };
}
