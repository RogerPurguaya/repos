
odoo.define('cashbox.main', function (require) {
"use strict";

var chrome = require('cashbox.chrome');
var core = require('web.core');

//core.action_registry.add('pos.ui', chrome.Chrome);
core.action_registry.add('cashbox.ui', chrome.Chrome);

});
