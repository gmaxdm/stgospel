
export const getWinSize = () => {
    return [window.innerWidth || document.documentElement.clientWidth,
            window.innerHeight || document.documentElement.clientHeight];
}
export const isInViewport = (r) => {
    // r: [top, right, bottom, left]
    const w = getWinSize();
    return r[0] >= 0 && r[3] >= 0 && r[1] <= w[0] && r[2] <= w[1];
}

export const declension = (num) => {
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
export const classNames = (classes) => {
   let _classes = [];
   for(const cls in classes) {
        if(classes[cls]) _classes.push(cls);
   }
   return _classes.join(" ");
}
export const tup2dict = (arr) => {
    let d = {};
    arr.forEach(t => d[t[0]] = t[1]);
    return d;
}
export const clone = (obj, src) => Object.assign(src || {}, obj);
export const objFromKeys = (arrObj, key) => arrObj.reduce((res, o) => clone({[o[key || "id"]]: o}, res), {});
export const emptyFromKeys = (obj) => Object.keys(obj).reduce((o, k) => clone({[k]: null}, o), {});
export const range = (num, start) => {
    return num <= 0 ? [] : Array.from(Array(num).keys(), start && (i => i + start));
}
export const isEmpty = (obj) => {
    if(Array.isArray(obj)) return !obj.length;
    return !Object.keys(obj).length;
}
export const last = (a) => a.length ? a[a.length-1] : null;
export const listIndexOf = (lt, obj, key) => {
    let idx = -1;
    for(let i=0; i<lt.length; i++) {
        if(lt[i] && lt[i][key] === obj[key]) {
            idx = i;
            break;
        }
    }
    return idx;
}
export const remove = (lt, val, key) => {
    const idx = key ? listIndexOf(lt, val, key) : lt.indexOf(val);
    if(idx > -1) {
        lt.splice(idx, 1);
        return 1;
    }
    return 0;
};
export const round = (num) => {
    // rounds by 2 points
    return Math.round((num + 0.0001) * 100) / 100;
}
export const percent = (val, prc) => {
	return round(val * prc / 100);
}

export const randint = (min, max) => {
    const m = Math.ceil(min);
    return ~~(Math.random() * (~~(max) - m + 1)) + m;
}

export const strtrunc = (s, lmt) => {
    if(s.length > lmt+3)
        return s.substr(0, lmt) + '...';
    return s;
}

export const groupby = (lt, key) => {
    // return in the same order as initial lt
    const d = {};
    lt.forEach((it, i) => {
        let p = d[it[key]];
        if(!p) p = d[it[key]] = [i, []];
        p[1].push(it);
    });
    return Object.values(d).sort((a, b) => a[0] - b[0]).map(a => a[1]);
}
export const ungroup = (lt) => {
    // return the flattern list of groupped list
    let l = [];
    lt.forEach(it => l = l.concat(it));
    return l;
}

export const url = (name, kw) => {
    const params = kw || {};
    return name + (name.indexOf("?") < 0 ? "?" : "&") + $.param(params);
}

export const dtformat = (sec) => {
	const rs = ~~(sec % 60);
    let min = ~~(sec / 60);
    let hrs = ~~(min / 60); min = min % 60;
    const dys = ~~(hrs / 24); hrs = hrs % 24;
    return (dys ? dys + " " + T.D + " " : "") + (hrs ? hrs + " " + T.H + " " : "") + (min ? min + " " + T.M + " " : "") + (rs ? rs + " " + T.S + " " : "");
}

export const zip = rows => rows[0].map((_, i) => rows.map(row => row[i]));

export const sum = arr => arr.reduce((s, n) => (s + n), 0);

export const max = arr => Math.max(...arr);
export const min = arr => Math.min(...arr);

export const tenth = (val) => ~~(val/10);

export const isIntersect = (a, b) => a.filter(i => b.includes(i)).length;

export function encode64(str) {
    // first we use encodeURIComponent to get percent-encoded Unicode,
    // then we convert the percent encodings into raw bytes which
    // can be fed into btoa.
    return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,
        function toSolidBytes(match, p1) {
            return String.fromCharCode('0x' + p1);
    }));
}
export function decode64(str) {
    // Going backwards: from bytestream, to percent-encoding, to original string.
    return decodeURIComponent(atob(str).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
}


export function post(url, data, cb) {
    $.post(url, data, (resp) => {
        cb && cb(resp);
    }, "json");
}

export const clean = (v) => parseInt(v) || 0;

