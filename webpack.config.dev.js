const {merge} = require('webpack-merge');
const base = require('./webpack.config.js');
const path = require('path');


module.exports = merge(base, {
    mode: "development",
    devtool: "source-map",
    devServer: {
        port: 2016,
        proxy: {
            '/': {
                target: "https://91.218.229.91",
                bypass: function(req, res, proxyOptions) {
                    if(req.url.indexOf('.bundle.js') > 0) {
                        console.log("[webpack devserver] " + req.url);
                    } else {
                        console.log("[webpack proxy] " + req.url);
                    }
                }
            }
        },
        after: function(app) {
            console.log("Listening http://locahost:2016");
        }
    }
});
