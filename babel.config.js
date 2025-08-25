module.exports = function(api) {
    api.cache(true);

    const presets = [
        "@babel/preset-react",
        "@babel/preset-env",
        ["minify", {
            builtIns: false
        }]
    ];

    return {
        presets
    };
}
