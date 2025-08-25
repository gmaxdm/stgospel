import React, {useState, useEffect} from 'react';

import {TooltipY} from './tooltip';
import {getMonth} from './models/calendar';
import {isEmpty, classNames, range, url} from './utils';
import {CALENDAR_MONTH_URL} from './models/urls';


function isEqDate(d1, d2) {
    return d1.getYear() === d2.getYear() && d1.getMonth() === d2.getMonth() && d1.getDate() === d2.getDate();
}


function chooseDir(i, j) {
    if(j < 2)
        return "right";
    if(j > 4)
        return "left";
    return "top";
}


function TrapezaImg({id, size, title}) {
    return (
        <div className={"trapeza-img" + (size ? "-" + size : "") + " tr-" + id} title={title} />
    );
}


const PLC = {c: range(35).map(i => ({}))};


export function CalendarView(props) {
    const today = new Date();

    const [month, setMonth] = useState(props.month || today.getMonth()+1);
    const [data, setData] = useState(PLC);
    const [day, setDay] = useState(props.day || 0);

    useEffect(() => {
        const t = $.get(url(CALENDAR_MONTH_URL, {m: month, d: day}), null, (d) => setData(d), "json");
        return () => {
            if(t) t.abort();
        };
    }, [month]);

    const rows = [];
    for(let i=0; i<data.c.length/7; i++) {
        rows.push(data.c.slice(i*7, (i+1)*7));
    }

    return (
        <div className="calendar container-sm mx-auto">
            <div className="row">
                <div className="col-6">
                    <select className="form-control form-control-sm" value={month} onChange={e => {setMonth(e.target.value); setDay(0);}}>
                        {range(12).map(i =>
                            <option key={i+1} value={i+1}>{getMonth(i+1)}</option>
                        )}
                    </select>
                </div>
            </div>
            <div className="row header">
                <div className="col">
                    Пн
                </div>
                <div className="col">
                    Вт
                </div>
                <div className="col">
                    Ср
                </div>
                <div className="col">
                    Чт
                </div>
                <div className="col">
                    Пт
                </div>
                <div className="col">
                    Сб
                </div>
                <div className="col text-danger">
                    Вс
                </div>
            </div>
            {rows.map((row, i) =>
                <div key={i} className="row">
                {row.map((c, j) => {
                    if(isEmpty(c)) {
                        return <div key={j} className="cal"><div className="date"/></div>
                    } else {
                        const d = new Date(c.date);
                        const holyday = c.title.length || j === 6;
                        return (
                            <div key={j} className="col">
                                <div className={classNames({
                                    "date": 1,
                                    "holyday": holyday,
                                    "easter": c.easter,
                                    "rip": c.rip,
                                    "carnival": c.carnival,
                                    "fast": !holyday && c.trapeza_id !== 1,
                                    "sel": month === d.getMonth()+1 && day === d.getDate(),
                                    "today": isEqDate(today, d)
                                })}>
                                    <TrapezaImg id={c.trapeza_id} size={32} title={c.trapeza}/>
                                    <TooltipY key={c.date} initiator={<span className={classNames({"text-muted-x": d.getMonth()+1 !== data.m, "twelve": c.twelve})}>{d.getDate()}</span>} dir={chooseDir(i, j)}>
                                        {c.title.map((p, i) => <h3 key={i} dangerouslySetInnerHTML={{__html: p}}/>)}
                                        {c.saints.map((p, i) => <p key={i} dangerouslySetInnerHTML={{__html: p}}/>)}
                                    </TooltipY>
                                    <div className="link"><a href={"/" + ["calendar", 1900+d.getYear(), d.getMonth()+1, d.getDate()].join("/")} title="перейти">&gt;&gt;</a></div>
                                </div>
                            </div>
                        );
                    }
                })}
                </div>
            )}
        </div>
    );
}
