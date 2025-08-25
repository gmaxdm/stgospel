const path = require('path');
const webpack = require('webpack');
const CircularDependencyPlugin = require('circular-dependency-plugin');
const TerserPlugin = require('terser-webpack-plugin');


module.exports = {
    mode: "production",
    entry: [
        './jsx/i18n/ru.jsx'
    ],
    output: {
        path: path.join(__dirname, "static"),
        filename: "js/i18n.ru.js",
        publicPath: "/static/",
        library: 'T',
        libraryTarget: 'var'
    },
    module: {
        rules: [
            {
                test: /\.jsx$/,
                loader: 'babel-loader',
                include: [
                    path.join(__dirname, 'jsx')
                ],
                options: {
                    presets: [
                    ],
                    plugins: [
                        '@babel/plugin-transform-runtime'
                    ]
                }
            }
        ]
    },
    plugins: [
        new CircularDependencyPlugin({
            exclude: /node_modules/,
            include: /jsx/,
            failOnError: true,
            allowAsyncCycles: false,
            cwd: process.cwd(),
        })
    ],
    resolve: {
        modules: [
            'node_modules',
            'jsx'
        ],
        extensions: [".js", ".jsx"]
    },
    optimization: {
        minimizer: [new TerserPlugin()],
    },
};
