import * as React from 'react';

interface IEnvironmentOption {
    id: string;
    name: string;
}

interface IEnvironmentSelectorProps {
    accounts: IEnvironmentOption[];
    selectedAccountId: string;
    environments: IEnvironmentOption[];
    selectedEnvironmentId: string;
    onAccountChange: (accountId: string) => void;
    onEnvironmentChange: (environmentId: string) => void;
    isLoading?: boolean;
}

/**
 * Account + environment dropdowns for selecting the target edit context.
 *
 * First dropdown: Client account (from listClientAccounts response).
 * Second dropdown: Environment (Test/Prod for selected account).
 * On change: triggers data reload via outcome in parent component.
 */
export const EnvironmentSelector: React.FC<IEnvironmentSelectorProps> = React.memo(
    ({
        accounts,
        selectedAccountId,
        environments,
        selectedEnvironmentId,
        onAccountChange,
        onEnvironmentChange,
        isLoading = false,
    }) => {
        const handleAccountChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
            onAccountChange(e.target.value);
        };

        const handleEnvironmentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
            onEnvironmentChange(e.target.value);
        };

        return (
            <div className="ee-env-selector" aria-label="Environment selection">
                <div className="ee-env-selector__group">
                    <label
                        htmlFor="ee-account-select"
                        className="ee-env-selector__label"
                    >
                        Account
                    </label>
                    <select
                        id="ee-account-select"
                        className="ee-env-selector__select"
                        value={selectedAccountId}
                        onChange={handleAccountChange}
                        disabled={isLoading || accounts.length === 0}
                        aria-label="Select account"
                    >
                        {accounts.length === 0 && (
                            <option value="">No accounts available</option>
                        )}
                        {accounts.map((acc) => (
                            <option key={acc.id} value={acc.id}>
                                {acc.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="ee-env-selector__group">
                    <label
                        htmlFor="ee-environment-select"
                        className="ee-env-selector__label"
                    >
                        Environment
                    </label>
                    <select
                        id="ee-environment-select"
                        className="ee-env-selector__select"
                        value={selectedEnvironmentId}
                        onChange={handleEnvironmentChange}
                        disabled={isLoading || environments.length === 0 || !selectedAccountId}
                        aria-label="Select environment"
                    >
                        {environments.length === 0 && (
                            <option value="">Select an account first</option>
                        )}
                        {environments.map((env) => (
                            <option key={env.id} value={env.id}>
                                {env.name}
                            </option>
                        ))}
                    </select>
                </div>

                {isLoading && (
                    <span className="ee-env-selector__loading" aria-live="polite">
                        Loading...
                    </span>
                )}
            </div>
        );
    },
);

EnvironmentSelector.displayName = 'EnvironmentSelector';
