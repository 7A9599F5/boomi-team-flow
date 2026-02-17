import * as React from 'react';
import { IObjectDataEntry } from '../types';

/**
 * Props injected by the wrapper HOC into the wrapped component.
 */
export interface IWrappedComponentProps {
    id: string;
    flowKey: string;
    model: ManywhoComponentModel;
    state: ManywhoComponentState;
    objectData: IObjectDataEntry[] | null;
    classes: string[];
}

/**
 * Raw props passed by Flow runtime to registered components.
 */
interface IFlowComponentProps {
    id: string;
    flowKey: string;
    // Flow may pass objectData directly on props (e.g. from template.html testing)
    objectData?: IObjectDataEntry[];
}

/**
 * Higher-Order Component wrapper for Boomi Flow custom components.
 *
 * Ported from the Boomi-PSO/ui-custom-component boilerplate pattern.
 * Bridges the Flow runtime (manywho.model, manywho.state) with a clean
 * component interface that receives typed props.
 *
 * Usage:
 *   manywho.component.register('MyComponent', component(MyComponent));
 */
export function component(
    WrappedComponent: React.ComponentType<IWrappedComponentProps>,
): React.ComponentType<IFlowComponentProps> {
    class FlowComponentWrapper extends React.Component<IFlowComponentProps> {
        render() {
            const { id, flowKey } = this.props;

            // Read model and state from Flow runtime globals
            const model = manywho.model.getComponent(id, flowKey);
            const state = manywho.state.getComponent(id, flowKey);
            const classes = manywho.styling.getClasses(
                '',
                id,
                'xml-diff-viewer',
                flowKey,
            );

            // objectData can come from model (normal Flow) or directly from props (testing)
            const objectData =
                model?.objectData ?? this.props.objectData ?? null;

            // Respect Flow visibility
            if (model && !model.isVisible) {
                return null;
            }

            return (
                <WrappedComponent
                    id={id}
                    flowKey={flowKey}
                    model={model}
                    state={state}
                    objectData={objectData}
                    classes={classes}
                />
            );
        }
    }

    return FlowComponentWrapper;
}
