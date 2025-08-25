const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');


module.exports = {
    devtool: "source-map",
    mode: "production",
    entry: [
        path.join(__dirname, "scss/main.scss")
    ],
    output: {
        path: path.join(__dirname, "static"),
        filename: "css/stgospel.bundle.css.js",
        publicPath: "/static/"
    },
    optimization: {
        minimizer: [
            new CssMinimizerPlugin()
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "css/stgospel.bundle.css"
        })
    ],
    module: {
        rules: [
            {
                test: /\.(scss|sass|css)$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    {
                        loader: "css-loader"
                    },
                    {
                        loader: "sass-loader",
                        options: {
                            implementation: require('sass')
                        }
                    }
                ]
            },
            {
                test: /\.(gif|jpg|jpeg|png|woff|woff2|eot|ttf|svg)(\?v=[\d\.]+)?$/,
                loader: "file-loader",
                options: {
                    name: "[name].[ext]",
                    outputPath: "img/"
                },
                include: [
                    path.join(__dirname, "static/images")
                ]
            }
        ]
    },
    resolve: {
        modules: [
            "scss"
        ],
        extensions: [".scss"]
    },
    resolveLoader: {
        modules: [
            "node_modules"
        ]
    }
};
