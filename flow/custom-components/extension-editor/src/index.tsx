import { component } from './utils/wrapper';
import { ExtensionEditor } from './ExtensionEditor';

declare const manywho: any;

// Register with Boomi Flow legacy runtime
manywho.component.register('ExtensionEditor', component(ExtensionEditor));
