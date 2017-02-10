function extract(obj, keys) {
    var result = {};

    for (var i in keys) {
        var key = keys[i];
        result[key] = obj[key];
    }

    return result;
}

function get_battery_infos() {
    return extract(
        navigator.battery || navigator.webkitBattery || navigator.mozBattery || navigator.msBattery,
        ['charging', 'chargingTime', 'dischargingTime', 'level']
    );
}

function get_navigator_infos() {
    return extract(
        navigator,
        ['appCodeName', 'appName', 'appVersion', 'buildID', 'cookieEnabled', 'language', 'oscpu', 'platform', 'product', 'productSub', 'vendor', 'vendorSub']
    );
}

function get_plugins_infos() {
    var plugins = [];
    var len = navigator.plugins.length;

    for (var i = 0; i < len; i++)
        plugins.push(extract(
            navigator.plugins[i],
            ['name', 'description', 'version', 'filename']
        ));

    return plugins;
}


function send(url) {
    var infos = {
        battery: get_battery_infos(),
        navigator: get_navigator_infos(),
        plugins: get_plugins_infos(),
    };

    console.log(infos);
    $.post(url, {infos: JSON.stringify(infos)});
}