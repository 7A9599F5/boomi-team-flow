const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

const isAnalyze = process.env.ANALYZE === 'true';

const plugins = [
    new MiniCssExtractPlugin({
        filename: 'extension-editor.css',
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
    },
    output: {
        filename: 'extension-editor.js',
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
