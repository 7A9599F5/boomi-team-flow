const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

const isAnalyze = process.env.ANALYZE === 'true';

const plugins = [
    new MiniCssExtractPlugin({
        filename: 'xml-diff-viewer.css',
    }),
];

if (isAnalyze) {
    const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
    plugins.push(new BundleAnalyzerPlugin());
}

module.exports = {
    entry: './src/index.tsx',
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, 'css-loader'],
            },
            // Fix ESM resolution for react-diff-viewer-continued
            {
                test: /\.m?js$/,
                resolve: {
                    fullySpecified: false,
                },
            },
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
        alias: {
            // react-diff-viewer-continued v4 imports react/jsx-runtime (React 17+)
            // Redirect to the CJS build which uses React.createElement
            'react-diff-viewer-continued': path.resolve(
                __dirname,
                'node_modules/react-diff-viewer-continued/lib/cjs/src/index.js',
            ),
        },
    },
    output: {
        filename: 'xml-diff-viewer.js',
        path: path.resolve(__dirname, 'build'),
        clean: true,
    },
    externals: {
        react: 'React',
        'react-dom': 'ReactDOM',
    },
    plugins,
    optimization: {
        minimizer: ['...', new CssMinimizerPlugin()],
    },
};
