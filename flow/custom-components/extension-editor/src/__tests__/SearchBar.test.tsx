/**
 * @jest-environment jsdom
 */
import * as React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SearchBar } from '../components/SearchBar';

// Advance timers for debounce testing
jest.useFakeTimers();

describe('SearchBar', () => {
    it('renders search input', () => {
        render(<SearchBar value="" onChange={jest.fn()} />);
        expect(screen.getByLabelText('Search extensions')).toBeInTheDocument();
    });

    it('shows placeholder text', () => {
        render(<SearchBar value="" onChange={jest.fn()} placeholder="Filter extensions" />);
        expect(screen.getByPlaceholderText('Filter extensions')).toBeInTheDocument();
    });

    it('does not show clear button when value is empty', () => {
        render(<SearchBar value="" onChange={jest.fn()} />);
        expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
    });

    it('shows clear button when value is non-empty', () => {
        render(<SearchBar value="Salesforce" onChange={jest.fn()} />);
        expect(screen.getByLabelText('Clear search')).toBeInTheDocument();
    });

    it('calls onChange after debounce delay', () => {
        const onChange = jest.fn();
        render(<SearchBar value="" onChange={onChange} />);
        const input = screen.getByLabelText('Search extensions');
        fireEvent.change(input, { target: { value: 'CRM' } });

        // Not called yet
        expect(onChange).not.toHaveBeenCalled();

        // Advance timers past debounce
        act(() => {
            jest.advanceTimersByTime(300);
        });
        expect(onChange).toHaveBeenCalledWith('CRM');
    });

    it('calls onChange with empty string when clear is clicked', () => {
        const onChange = jest.fn();
        render(<SearchBar value="test" onChange={onChange} />);
        fireEvent.click(screen.getByLabelText('Clear search'));
        expect(onChange).toHaveBeenCalledWith('');
    });

    it('has search role', () => {
        render(<SearchBar value="" onChange={jest.fn()} />);
        expect(screen.getByRole('search')).toBeInTheDocument();
    });
});
