String.prototype.hash = function() {
	var h = 0;
	if(this.length === 0) return h;
	for(var i=0; i<this.length; i++) {
		var chr = this.charCodeAt(i);
		h = ((h << 5) - h) + chr;
		h |= 0;
	}
	return h;
};
String.prototype.random = function(N) {
	N = N || 8;
	return this + (Math.random().toString(36)+'0000000000000000')
				   .slice(2, N+2);
};
// Warn if overriding existing method
if(Array.prototype.equals)
    console.warn("Overriding existing Array.prototype.equals. Possible causes: New API defines the method, there's a framework conflict or you've got double inclusions in your code.");
Array.prototype.equals = function(array) {
    if (!array)
        return false;
    if (this.length != array.length)
        return false;
    for (var i = 0, l=this.length; i < l; i++) {
        // Check if we have nested arrays
        if (this[i] instanceof Array && array[i] instanceof Array) {
            // recurse into the nested arrays
            if (!this[i].equals(array[i]))
                return false;
        } else if (this[i] != array[i]) {
            // Warning - two different object instances will never be equal: {x:20} != {x:20}
            return false;
        }
    }
    return true;
}
// Hide method from for-in loops
Object.defineProperty(Array.prototype, "equals", {enumerable: false});

if(!Array.prototype.includes) {
    Array.prototype.includes = function(value) {
        for(var i=0; i<this.length; i++) {
            if(this[i] === value) return true;
        }
        return false;
    }
}
if(!Object.values) {
    Object.defineProperty(Object, 'values', {
        enumerable: true,
        configurable: true,
        writable: true,
        value: function(target) {
            'use strict';
            if(target === undefined || target === null) {
                throw new TypeError('Cannot convert first argument to object');
            }
            return Object.keys(target).map(function(k) {return target[k]});
        }
    });
}
if(!Object.assign) {
    Object.defineProperty(Object, 'assign', {
        enumerable: false,
        configurable: true,
        writable: true,
        value: function(target) {
            'use strict';
            if(target === undefined || target === null) {
                throw new TypeError('Cannot convert first argument to object');
            }

            var to = Object(target);
            for(var i = 1; i < arguments.length; i++) {
                var nextSource = arguments[i];
                if(nextSource === undefined || nextSource === null) {
                    continue;
                }
                nextSource = Object(nextSource);

                var keysArray = Object.keys(Object(nextSource));
                for(var nextIndex = 0, len = keysArray.length; nextIndex < len; nextIndex++) {
                    var nextKey = keysArray[nextIndex];
                    var desc = Object.getOwnPropertyDescriptor(nextSource, nextKey);
                    if(desc !== undefined && desc.enumerable) {
                        to[nextKey] = nextSource[nextKey];
                    }
                }
            }
            return to;
        }
    });
}

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
	    var cookies = document.cookie.split(';');
	    for (var i = 0; i < cookies.length; i++) {
		    var cookie = jQuery.trim(cookies[i]);
		    if(cookie.substring(0, name.length + 1) == (name + '=')) {
		        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
		        break;
		    }
	    }
	}
	return cookieValue;
} 
function csrfSafeMethod(method) {
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if(!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        }
    }
});

function strtrunc(s, lmt) {
    if(s.length > lmt+3)
        return s.substr(0, lmt) + '...';
    return s;
}
function current_timestamp_ms() {
    var dt = new Date();
    return dt.getTime();
}
function current_timestamp() {
    return Math.floor(current_timestamp_ms() / 1000);
}
function dtformat(sec) {
	var rs = Math.floor(sec % 60);
    var min = Math.floor(sec / 60);
    var hrs = Math.floor(min / 60); min = min % 60;
    var dys = Math.floor(hrs / 24); hrs = hrs % 24;
    return (dys ? dys + " д " : "") + (hrs ? hrs + " ч " : "") + (min ? min + " мин " : "") + (rs ? rs + " сек " : "");
}
if(!Date.prototype.addDays) {
    Date.prototype.addDays = function(days) {
        var dat = new Date(this.valueOf());
        dat.setDate(dat.getDate() + days);
        return dat;
    }
}
var DATE_FORMAT = "yy-mm-dd";
var MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
var MONTHS_FULL = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"];
var DAYS = ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"];
function rus_date(dt, full) {
    return dt.getDate() + " " + (full ? MONTHS_FULL[dt.getMonth()] : MONTHS[dt.getMonth()]) + " " + (dt.getYear() + 1900);
}
function rus_date_day(dt) {
    return DAYS[dt.getDay()];
}
function iso_date(dt) {
    if(!dt) return null;
    var year = dt.getYear() + 1900;
    var month = dt.getMonth() + 1;
    var day = dt.getDate();
    return year + "-" + (month.length == 1 ? "0" : "") + month + "-" + (day.length == 1 ? "0" : "") + day;
}
function getDate(dtstr) {
    var dt;
    try {
        dt = $.datepicker.parseDate(DATE_FORMAT, dtstr);
    } catch(error) {
        dt = null;
    }
    return dt;
}
function copyToClipboard(text) {
    var inp = document.createElement("input");
    inp.setAttribute("value", text);
    document.body.appendChild(inp);
    inp.contentEditable = true;
    inp.readOnly = false;
    inp.select();
    var range = document.createRange();
    range.selectNodeContents(inp);
    var s = window.getSelection();
    s.removeAllRanges();
    s.addRange(range);
    inp.setSelectionRange(0, 1000000);
    document.execCommand("copy");
    document.body.removeChild(inp);
}
function declension(num) {
	if(num < 1) return 2;
	if(num > 100) num %= 100;
	if(num > 10 && num < 15) return 2;
	else {
		num %= 10;
		if(num == 0 || (num >= 5 && num <= 9)) return 2;
		else if(num == 1) return 0;
		else if (num >= 2 && num <= 4) return 1;
	}
}
function round(num) {
    // rounds by 2 points
    return Math.round((num + 0.0001) * 100) / 100;
}
function percent(val, prc) {
	return val * prc / 100;
}
function is_function(obj) {
    return !!(obj && obj.constructor && obj.call && obj.apply);
}
var MODALDIALOG = null;

function raise_error(text) {
    $(".top-messages").append(
        '<li class="alert alert-danger" role="alert">'+text+'</li>'
    );
}
