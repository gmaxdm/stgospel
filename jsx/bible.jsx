import React from 'react';

import {ActionIcon} from './components';


const ID_PH = "777";


export const BIBLE_DEPTH = {
    BOOK: 0,
    CHAPTER: 1,
    LINE: 2
}


class Model {
    constructor(props) {
        this.data = props;

        this.toString = this.toString.bind(this);
    }

    toString() {}
}


export class Book extends Model {
    constructor(props) {
        super(props);
        this.url = URLS.BOOK.replace(ID_PH, props.id);
        this.key = "chapters";
    }

    toString() {
        return this.data.title;
    }
}


export class Chapter extends Model {
    constructor(props) {
        super(props);
        this.url = URLS.CHAPTER.replace(ID_PH, props.book_id).replace(ID_PH, props.num);
        this.key = "lines";
    }

    toString() {
        return "Глава " + this.data.num;
    }
}


export class Line extends Model {

    toString() {
        return this.data.num + " " + this.data.text;
    }
}


export class Volume {
    constructor(props) {
        this.books = props.books;
        this.ch_col = props.ch_col;
        this.creater = props.volume.creater;
        this.id = props.volume.id;
        this.public = props.volume.public;
        this.title = props.volume.title;

        this.queue = this.queue.bind(this);
    }

    queue(step) {
        step = step || 1;
        let idx = 1;
        let lt = [];
        let _prev = [];
        this.books.forEach((book) => {
            let _k = 1;
            let _sh = _prev.length;
            let ch_cnt = book.chapters + _sh;
            if(book.has_foreword) ch_cnt--;
            const val = Math.floor(ch_cnt / step);
            const rem = (val === 0 ? book.chapters : ch_cnt % step);
            for(let i=0; i < val; i++) {
                let _books = [];
                if(_prev.length) {
                    _books = _prev;
                    _prev = [];
                }
                const qi = {
                    id: idx++,
                    item: _books,
                };
                if(i == 0 && book.has_foreword) {
                    qi.item.push({book: book, num: i});
                }
                let _step = step;
                if(_sh) {
                    _step = _step - _sh;
                    _sh = 0;
                }
                for(let j=0; j < _step; j++) {
                    qi.item.push({book: book, num: _k++});
                }
                lt.push(qi);
            }
            if(rem) {
                for(let j=0; j<rem; j++) {
                    _prev.push({book: book, num: _k++});
                }
            }
        });
        if(_prev.length) {
            lt.push({
                id: idx++,
                item: _prev,
            });
        }
        Object.values(this.ch_col).forEach((ch) => {
            const qi = {
                id: idx++,
                item: [],
            }
            ch.chapters.forEach((item) => {
                qi.item.push({book: {title: item.book_title} , num: item.num});
            });
            lt.push(qi);
        });
        return lt;
    }
}


export class QueueItemComponent extends React.Component {
    render() {
        const data = this.props.data;
        return (
            <React.Fragment>
                <div>{data.id}.&nbsp;{data.title}</div>
                {data.title ? null :
                    <ul className="list-unstyled">
                    {data.item.map((it, i) => 
                        <li key={it.book.id + "_" + i}>{it.book.title}.&nbsp;{it.num ? <span>Глава {it.num}</span> : <span>Предисловие</span>}</li>
                    )}
                    </ul>
                }
            </React.Fragment>
        );
    }
}


export class BookComponent extends React.Component {
    constructor(props) {
        super(props);
        this.item = new Book(props.data);
    }

    render() {
        return (
            <span>
                <i className="fas fa-book" />&nbsp;
                {this.item.toString()}
            </span>
        );
    }
}


export class ChapterComponent extends React.Component {
    constructor(props) {
        super(props);
        this.item = new Chapter(props.data);
    }

    render() {
        let item = this.item.toString();
        if(this.props.fullName && this.props.data.book_title) {
            item += " (" + this.props.data.book_title + ")";
        }
        return (
            <span>
                <i className="fab fa-readme" />&nbsp;{item}
            </span>
        );
    }
}


export class LineComponent extends React.Component {
    constructor(props) {
        super(props);
        this.item = new Line(props.data);
    }

    render() {
        const data = this.item.data;
        return (
            <span>
                {data.num ? <strong className="text-danger">{data.num} </strong> : null}
                {data.text}
            </span>
        );
    }
}


export class PrayComponent extends React.Component {
    render() {
        return (
            <span>
                <i className="fab fa-leanpub" />&nbsp;
                {this.props.data.title}
            </span>
        );
    }
}


const BIBLE_TREE = [
    {model: Book, component: BookComponent},
    {model: Chapter, component: ChapterComponent},
    {model: Line, component: LineComponent}
];


export class WalkBibleTree extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            depth: 0,
            cur_val: null,
            back_val: null,
            selected: {},
        }
        this.values = props.values;
        this.cache = {
            0: props.values,
            1: {},
        };

        this.walk = this.walk.bind(this);
        this.back = this.back.bind(this);
        this.ok = this.ok.bind(this);
    }

    walk(val) {
        const depth = this.state.depth;
        if(depth < this.props.depth) {
            const next_depth = depth + 1;
            const model = new BIBLE_TREE[depth].model(val);
            let values = this.cache[next_depth][val.id];
            if(values) {
                this.setState((pS) => {
                    this.values = values;
                    return {depth: pS.depth + 1, back_val: pS.cur_val, cur_val: val};
                });
            } else {
                $.ajax({
                    url: model.url,
                    type: "GET",
                    success: (res) => {
                        values = this.cache[next_depth][val.id] = res[model.key];
                        this.setState((pS) => {
                            if(pS.depth != depth) return null;
                            this.values = values;
                            this.cache[next_depth+1] = {};
                            return {depth: pS.depth + 1, back_val: pS.cur_val, cur_val: val};
                        });
                    },
                    dataType: "json"
                });
            }
        } else {
            this.setState((pS) => {
                const sel = pS.selected;
                if(sel[val.id]) {
                    delete sel[val.id];
                } else {
                    sel[val.id] = val;
                }
                return sel;
            });
        }
    }

    back() {
        this.setState((pS) => {
            const depth = pS.depth;
            if(pS.back_val) {
                this.values = this.cache[depth-1][pS.back_val.id];
            } else {
                this.values = this.cache[depth-1];
            }
            return {depth: depth - 1, back_val: null, cur_val: pS.back_val};
        });
    }

    ok() {
        this.props.onSelect(this.state.selected);
    }

    render() {
        const depth = this.state.depth;
        const bottom = depth === (this.props.depth || 0);
        const Component = BIBLE_TREE[depth].component;
        const el = (depth > 0 ? new BIBLE_TREE[depth-1].model(this.state.cur_val) : null);
        return (
            <React.Fragment>
                {el ?
                    <div className="d-flex">
                        <div><ActionIcon onClick={this.back} icon="fas fa-chevron-circle-left" /></div>
                        <div className="bibletree__title">{el.toString()}</div>
                    </div>
                : null}
                <p className="text-right"><ActionIcon onClick={this.ok} disabled={!Object.keys(this.state.selected).length} icon="fas fa-check-circle" /></p>
                <ul className="list-unstyled select__items">
                    {this.values.map((val, i) =>
                        <li key={i} onClick={(e) => this.walk(val)} className={bottom && this.state.selected[val.id] ? "selected" : ""}><Component data={val} /></li>
                    )}
                </ul>
            </React.Fragment>
        );
    }
}

