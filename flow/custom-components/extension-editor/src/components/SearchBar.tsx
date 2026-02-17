import * as React from 'react';
import { useState, useCallback, useRef, useEffect } from 'react';

interface ISearchBarProps {
    value: string;
    onChange: (query: string) => void;
    placeholder?: string;
}

const DEBOUNCE_MS = 300;

/**
 * Debounced search bar for filtering extension tree nodes.
 *
 * Features:
 * - Input field with search icon
 * - Debounced onChange (300ms) to avoid excessive re-renders
 * - Clear button when query is non-empty
 * - Controlled externally via value/onChange
 */
export const SearchBar: React.FC<ISearchBarProps> = React.memo(
    ({ value, onChange, placeholder = 'Search extensions...' }) => {
        const [localValue, setLocalValue] = useState(value);
        const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

        // Sync external value changes into local state (e.g. RESET action)
        useEffect(() => {
            setLocalValue(value);
        }, [value]);

        const handleChange = useCallback(
            (e: React.ChangeEvent<HTMLInputElement>) => {
                const next = e.target.value;
                setLocalValue(next);
                if (timerRef.current !== null) {
                    clearTimeout(timerRef.current);
                }
                timerRef.current = setTimeout(() => {
                    onChange(next);
                }, DEBOUNCE_MS);
            },
            [onChange],
        );

        const handleClear = useCallback(() => {
            if (timerRef.current !== null) {
                clearTimeout(timerRef.current);
            }
            setLocalValue('');
            onChange('');
        }, [onChange]);

        // Clean up timer on unmount
        useEffect(() => {
            return () => {
                if (timerRef.current !== null) {
                    clearTimeout(timerRef.current);
                }
            };
        }, []);

        return (
            <div className="ee-search-bar" role="search">
                <span className="ee-search-bar__icon" aria-hidden="true">
                    &#128269;
                </span>
                <input
                    type="search"
                    className="ee-search-bar__input"
                    value={localValue}
                    onChange={handleChange}
                    placeholder={placeholder}
                    aria-label="Search extensions"
                />
                {localValue && (
                    <button
                        type="button"
                        className="ee-search-bar__clear"
                        onClick={handleClear}
                        aria-label="Clear search"
                    >
                        &times;
                    </button>
                )}
            </div>
        );
    },
);

SearchBar.displayName = 'SearchBar';
