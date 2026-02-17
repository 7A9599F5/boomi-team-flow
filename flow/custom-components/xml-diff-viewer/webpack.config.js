const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
    entry: './src/index.tsx',
    devtool: 'inline-source-map',
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader'],
            },
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
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
    plugins: [
        new HtmlWebpackPlugin({
            template: './template.html',
        }),
    ],
    devServer: {
        static: path.join(__dirname, 'build'),
        port: 8080,
        hot: true,
    },
};
