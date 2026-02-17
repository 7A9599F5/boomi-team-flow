/**
 * @jest-environment jsdom
 */
import { renderHook, act } from '@testing-library/react-hooks';
import { useClipboard } from '../hooks/useClipboard';

describe('useClipboard', () => {
    beforeEach(() => {
        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.useRealTimers();
        jest.restoreAllMocks();
    });

    it('starts with idle status', () => {
        const { result } = renderHook(() => useClipboard());
        expect(result.current.status).toBe('idle');
    });

    it('sets status to copied on success', async () => {
        const writeText = jest.fn().mockResolvedValue(undefined);
        Object.assign(navigator, {
            clipboard: { writeText },
        });

        const { result, waitForNextUpdate } = renderHook(() => useClipboard());

        act(() => {
            result.current.copy('test text');
        });

        await waitForNextUpdate();

        expect(writeText).toHaveBeenCalledWith('test text');
        expect(result.current.status).toBe('copied');
    });

    it('resets status to idle after 2 seconds', async () => {
        const writeText = jest.fn().mockResolvedValue(undefined);
        Object.assign(navigator, {
            clipboard: { writeText },
        });

        const { result, waitForNextUpdate } = renderHook(() => useClipboard());

        act(() => {
            result.current.copy('test');
        });

        await waitForNextUpdate();
        expect(result.current.status).toBe('copied');

        act(() => {
            jest.advanceTimersByTime(2000);
        });

        expect(result.current.status).toBe('idle');
    });

    it('sets status to error on clipboard failure', async () => {
        const writeText = jest
            .fn()
            .mockRejectedValue(new Error('Permission denied'));
        Object.assign(navigator, {
            clipboard: { writeText },
        });

        const { result, waitForNextUpdate } = renderHook(() => useClipboard());

        act(() => {
            result.current.copy('test');
        });

        await waitForNextUpdate();
        expect(result.current.status).toBe('error');
    });

    it('falls back to execCommand when clipboard API unavailable', () => {
        Object.assign(navigator, { clipboard: undefined });
        const execCommand = jest.fn().mockReturnValue(true);
        document.execCommand = execCommand;

        const { result } = renderHook(() => useClipboard());

        act(() => {
            result.current.copy('fallback text');
        });

        expect(execCommand).toHaveBeenCalledWith('copy');
        expect(result.current.status).toBe('copied');
    });
});
