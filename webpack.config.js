var path = require('path');
var webpack = require('webpack');
var CircularDependencyPlugin = require('circular-dependency-plugin');


module.exports = {
    mode: "production",
    entry: [
        './jsx/main.jsx'
    ],
    output: {
        path: path.join(__dirname, "static"),
        filename: "js/gospel.bundle.js",
        publicPath: "/static/"
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
    }
};
