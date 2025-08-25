import React, {useState, useRef, useEffect} from 'react';

import {url, clone} from './utils';


export const Loader = () => <div className="loading"/>;


export default function loaded(Component, urlsConf) {
    return function (props) {
        const _urls = {};
        Object.keys(urlsConf).forEach(k => _urls[k] = 0);

        const [urls, setUrls] = useState(_urls);
        const data = useRef({});
        const get = useRef({});

        useEffect(() => {
            for(const k in urlsConf) {
                const [baseurl, kwargs] = urlsConf[k];
                get.current[k] = $.get(url(baseurl, kwargs), null, (d) => {
                    data.current[k] = d;
                    setUrls(pu => {
                        const _u = clone(pu);
                        _u[k] = 1;
                        return _u;
                    });
                }, "json");
            }

            return () => {
                for(const k in get.current) {
                    if(get.current[k]) get.current[k].abort();
                }
            };
        }, []);

        if(Object.values(urls).every(e => e)) 
            return <Component {...data.current} {...props} />;
        return <Loader/>;
    }
}

