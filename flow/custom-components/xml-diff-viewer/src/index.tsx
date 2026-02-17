import { component } from './utils/wrapper';
import { XmlDiffViewer } from './XmlDiffViewer';

// Register with Boomi Flow legacy runtime
manywho.component.register('XmlDiffViewer', component(XmlDiffViewer));
