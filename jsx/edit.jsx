import React from 'react';

import {ActionIcon, DialogIcon, MultiList,
        DefaultComponent, Calendar} from './components';
import {WalkBibleTree} from './bible';
import {post} from './utils';


export class Loading extends React.Component {
    render() {
        return <div className="loading" />;
    }
}


export const loaded = (Component, urlsConf) => {
    return class extends React.Component {
        constructor(props) {
            super(props);
            this.state = {
                loading: true
            }
            Object.keys(urlsConf).forEach(k => this.state[k] = false);
            this.data = {};

            this.addState = this.addState.bind(this);
        }

        addState(urlKey) {
            this.setState((pS) => {
                const _st = Object.assign({}, pS);
                _st[urlKey] = true;
                _st.loading = false;
                Object.keys(urlsConf).forEach((k) => {
                    _st.loading = _st.loading || !_st[k]
                });
                return _st;
            });
        }

        componentDidMount() {
            for(const urlKey in urlsConf) {
                const url = urlsConf[urlKey];
                $.ajax({
                    url: url,
                    type: "GET",
                    success: (data) => {
                        this.data[urlKey] = data;
                        this.addState(urlKey);
                    },
                    dataType: "json"
                });
            }
        }

        render() {
            if(this.state.loading) return <Loading />;
            return <Component {...this.data} {...this.props} />;
        }
    }
};


export class NameEdit extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            change_name: false,
            name: props.name,
        }

        this.keyPress = this.keyPress.bind(this);
        this.setName = this.setName.bind(this);
        this.saveName = this.saveName.bind(this);
        this.changeName = this.changeName.bind(this);
    }

    keyPress(e) {
        if(e.key === "Enter") {
            this.saveName();
        }
    }

    changeName(e) {
        this.setState((pS) => ({
            change_name: !pS.change_name
        }));
    }

    setName(name) {
        this.setState({name: name, change_name: false},
        () => {if(this.props.onSave) this.props.onSave(name)});
    }

    saveName() {
        const name = this.name.value.substr(0, (this.props.maxLength || 100));
        if(name === this.state.name) {
            this.setState({change_name: false});
            return;
        }
        if(this.props.remoteSave) {
            this.props.remoteSave(name, (res) => {
                if(res.ok) {
                    this.setName(name);
                }
            });
            return;
        }
        this.setName(name);
    }

    render() {
        if(this.state.change_name) {
            return (
                <span>
                    <input type="text" disabled={this.props.disabled} defaultValue={this.state.name} placeholder={this.props.placeholder || "введите название"} onKeyPress={this.keyPress} name="name" ref={(i) => this.name = i} />&nbsp;
                    {this.props.disabled ? null :
                    <React.Fragment>
                    <ActionIcon onClick={this.changeName} icon="fas fa-ban" />&nbsp;
                    <ActionIcon onClick={this.saveName} icon="fas fa-check-circle" />
                    </React.Fragment>
                    }
                </span>
            );
        }
        return (
            <span>{this.state.name} <ActionIcon disabled={this.props.disabled} onClick={this.changeName} title={this.props.title} icon="far fa-edit" /></span>
        );
    }
}


export class ListEdit extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            list: props.list || [],
            sorting: false,
        }

        this.onSort = this.onSort.bind(this);
        this.onChange = this.onChange.bind(this);
        this.dispatchAdd = this.dispatchAdd.bind(this);
        this.dispatchRemove = this.dispatchRemove.bind(this);
        this.add = this.add.bind(this);
        this.remove = this.remove.bind(this);
        this.postAdd = this.postAdd.bind(this);
        this.postRemove = this.postRemove.bind(this);
        this.setSorting = this.setSorting.bind(this);

        if(props.dialog === "bibletree") {
            this.innerDialog = (
                <WalkBibleTree values={props.addValues} depth={props.depth} onSelect={this.dispatchAdd} />
            );
        } else {
            this.innerDialog = null;
        }
    }

    componentWillUnmount() {
        if(this.state.sorting) {
            $(this.sortable).sortable("destroy");
        }
    }

    setSorting() {
        this.setState((pS) => ({
            sorting: !pS.sorting
        }), () => {
            if(this.state.sorting) {
                $(this.sortable).sortable({
                    stop: this.onSort,
                });
            } else {
                $(this.sortable).sortable("destroy");
            }
        });
    }

    onSort() {
        if(!this.props.sortAction) return;
        const seria = $(this.sortable).sortable("toArray", {'attribute': 'data-order'});
        post(this.props.url, {
            id: this.props.id,
            sub_id: this.props.sub_id,
            action: this.props.sortAction,
            seria: seria.join(','),
        }, (res) => {
            if(res.ok) {
                this.setState((pS) => {
                    let nl = [];
                    seria.forEach((i) => {
                        nl.push(pS.list[i-1]);
                    });
                    return {
                        list: nl
                    };
                });
            }
        });
    }

    onChange() {
        if(this.props.onChange) {
            if(this.props.single) {
                this.props.onChange(this.state.list[0]);
            } else {
                this.props.onChange(this.state.list);
            }
        }
    }

    dispatchAdd(items) {
        const sels = Object.values(items);
        if(!sels.length) return;
        if(this.props.url) {
            const ids = Object.keys(items);
            this.postAdd(ids, sels);
        } else {
            this.add(sels);
        }
    }

    add(sels) {
        this.dialog.close();
        if(this.props.single) {
            this.setState({
                list: sels
            }, this.onChange);
        } else {
            this.setState((pS) => ({
                list: pS.list.concat(sels)
            }), this.onChange);
        }
    }

    postAdd(ids, sels) {
        const data = {
            id: this.props.id,
            sub_id: this.props.sub_id,
            action: this.props.addAction,
            len: this.state.list.length,
        };
        data[this.props.itemKey] = ids;
        post(this.props.url, data, (res) => {
            if(res.ok) {
                this.add(sels);
            } else {
                raise_error("Не удается добавить. Возможно, уже добавлено.");
            }
        });
    }

    dispatchRemove(item, i) {
        if(!item) return;
        if(this.props.url) {
            this.postRemove(item, i);
        } else {
            this.remove(i);
        }
    }

    remove(i) {
        this.setState((pS) => {
            let lt = pS.list;
            lt.splice(i, 1);
            return {
                list: lt
            };
        }, this.onChange);
    }

    postRemove(item, i) {
        const data = {
            id: this.props.id,
            sub_id: this.props.sub_id,
            action: this.props.removeAction
        };
        data[this.props.itemKey] = item.id;
        post(this.props.url, data, (res) => {
            if(res.ok) {
                this.remove(i);
            } else {
                raise_error("Не удается удалить. Возможно, уже удалено.");
            }
        });
    }

    render() {
        const Component = this.props.component || DefaultComponent;
        const inForm = !this.props.url && this.props.itemKey;
        return (
            <div className="list__cont">
                <ul className="list-unstyled" ref={u => this.sortable = u} >
                    {this.state.list.map((it, i) =>
                        <li key={it.id} data-order={i+1}>
                            {inForm ? <input type="hidden" name={this.props.itemKey} value={it.id} /> : null}
                            <Component data={it} fullName />&nbsp;
                            {this.props.single ? null : <ActionIcon disabled={this.props.disabled} onClick={() => this.dispatchRemove(it, i)} icon="fas fa-times" />}
                        </li>
                    )}
                </ul>
                <p><DialogIcon
                        disabled={this.props.disabled}
                        ref={d => this.dialog = d}
                        icon="fas fa-plus-circle"
                        text={this.props.text || (this.props.single ? "Выбрать" : "Добавить")}
                        inner={this.innerDialog || <MultiList single={this.props.single} values={this.props.addValues} component={this.props.component} onSelect={this.dispatchAdd} />} /></p>
                {this.props.sortAction ?
                    <p>
                        <ActionIcon className={"badge badge-" + (this.state.sorting ? "warning" : "secondary")} icon="fas fa-sort" onClick={this.setSorting} text="Сортировать" />
                    </p>
                : null}
            </div>
        );
    }
}


export class CollectionEdit extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            cols: props.collection
        }

        this.create = this.create.bind(this);
        this.delCol = this.delCol.bind(this);
        this.changeColName = this.changeColName.bind(this);
    }

    create() {
        post(this.props.url, {
            id: this.props.id,
            action: this.props.newAction,
            name: "",
            order: Object.keys(this.state.cols).length,
        }, (res) => {
            if(res.ok) {
                const pk = res.ok;
                this.setState((pS) => {
                    const cols = pS.cols;
                    cols[pk] = {
                        id: pk,
                        title: ""
                    };
                    cols[pk][this.props.listKey] = [];
                    return {cols: cols};
                });
            }
        });
    }

    changeColName(col, name, cb) {
        post(this.props.url, {
            id: this.props.id,
            sub_id: col.id,
            action: this.props.nameAction,
            name: name
        }, (res) => {
            if(cb) cb(res);
            this.setState((pS) => {
                const cols = pS.cols;
                cols[col.id].title = name;
                return {cols: cols};
            });
        });
    }

    delCol(col) {
        if(confirm("Вы действительно хотите удалить все собрание с внутренними коллекциями?")) {
            post(this.props.url, {
                id: this.props.id,
                sub_id: col.id,
                action: this.props.deleteAction
            }, (res) => {
                if(res.error) {
                    return;
                }
                this.setState((pS) => {
                    const cols = pS.cols;
                    delete cols[col.id];
                    return {cols: cols};
                });
            });
        }
    }

    render() {
        const collections = Object.values(this.state.cols);
        return (
            <>
                <div className="collection__cont pb-2">
                    {collections.map((col) =>
                        <div key={col.id} className="collection">
                            <h5 className="mt-2"><NameEdit remoteSave={(name, cb) => this.changeColName(col, name, cb)} name={col.title} />&nbsp;<ActionIcon onClick={() => this.delCol(col)} icon="fas fa-times" title="Удалить собрание" /></h5>
                            <ListEdit
                                url={this.props.url}
                                id={this.props.id}
                                sub_id={col.id}
                                dialog={this.props.dialog}
                                list={col[this.props.listKey]}
                                component={this.props.component}
                                addValues={this.props.addValues}
                                depth={this.props.depth}
                                itemKey={this.props.itemKey}
                                addAction={this.props.addAction}
                                removeAction={this.props.removeAction} />
                        </div>
                    )}
                </div>
                <p className="mt-3">
                    <ActionIcon onClick={this.create} icon="fas fa-plus-circle" text="Добавить" />
                </p>
            </>
        );
    }
}


export const LIST_TYPE_NAME = {
    "H": "health",
    "R": "rip",
    "S": "sick",
    "W": "war",
    "P": "pray",
    "A": "army",
};
export const init_lists = () => {
    const res = {};
    Object.values(LIST_TYPE_NAME).forEach(s => {res[s] = [];});
    return res;
};

export const init_div = (it) => {
    let _div = {
        id: it.id,
        name: it.name,
        order: it.order || 0
    };
    Object.assign(_div, init_lists());
    return _div;
};


export class PrayForCard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sorting: false,
        };

        this.dialog = {}

        this.setDate = this.setDate.bind(this);
        this.setSorting = this.setSorting.bind(this);
        this.sort = this.sort.bind(this);
    }

    componentWillUnmount() {
        if(this.state.sorting) {
            $(this.sortable).sortable("destroy");
        }
    }

    setSorting() {
        this.setState((pS) => ({
            sorting: !pS.sorting
        }), () => {
            if(this.state.sorting) {
                $(this.sortable).sortable({
                    stop: this.sort,
                });
            } else {
                $(this.sortable).sortable("destroy");
            }
        });
    }

    sort() {
        if(this.props.onSort) {
            const seria = $(this.sortable).sortable("toArray", {'attribute': 'data-order'});
            this.props.onSort(this.props.card, this.props.listType, seria);
        }
    }

    setDate(pf, date) {
        this.dialog[pf.id].close();
        this.props.onChangeTill(pf, date);
    }

    render() {
        const card = this.props.card;
        const listKey = LIST_TYPE_NAME[this.props.listType];
        const lt = card[listKey];
        const health = this.props.listType === "H";
        const names = this.props.names || ["имя", "имени"];
        return (
            <div className="card bg-light mb-3">
                <div className="card-num"><span className="badge badge-secondary">{this.props.num}</span></div>
                {this.props.disabled || !this.props.onRemove ? null :
                <div className="card-remove"><ActionIcon onClick={() => this.props.onRemove(card)} icon="fas fa-minus-square" /></div>}
                {health && this.props.onChangeHeader ?
                    <div className="card-header">
                        <NameEdit placeholder={"введите " + names[0]} remoteSave={(name, cb) => this.props.onChangeHeader(card, name, cb)} maxLength={200} name={card.name} disabled={this.props.disabled} />&nbsp;
                    </div>
                : null}
                <div className="card-body">
                    {this.props.hint ? <p className="muted"><small>{this.props.hint}</small></p> : null}
                    <ul className="card-text list-unstyled" ref={u => this.sortable = u}>
                        {lt.map((n, i) =>
                            <li key={n.id} data-order={i+1} className={(n.till && this.props.today > n.till) ? "text-danger" : ""}>
                                <span className="text-muted">{i+1}.</span>&nbsp;
                                <NameEdit placeholder={"введите "+ names[0]} title={"редактировать " + names[0]} remoteSave={(name, cb) => this.props.onChangeName(n, name, cb)} name={n.name} disabled={this.props.disabled} />&nbsp;
                                {n.till ? <small className="text-muted">(до {rus_date(n.till)}) </small> : null}
                                {this.props.disabled ? null :
                                <React.Fragment>
                                <DialogIcon
                                    ref={d => this.dialog[n.id] = d}
                                    title={"изменить дату завершения поминания для этого " + names[1]}
                                    icon="far fa-calendar-alt"
                                    inner={<Calendar nullable defaultValue={n.till} onSelect={(date) => this.setDate(n, date)} />} />&nbsp;
                                <ActionIcon onClick={() => this.props.onRemName(card, n, i, listKey, "удалить " + names[0])} title={"удалить " + names[0]} icon="far fa-minus-square" />
                                </React.Fragment>
                                }
                            </li>
                        )}
                    </ul>
                    {!this.props.disabled && (this.props.limit === 0 || lt.length < this.props.limit) ?
                        <div><ActionIcon onClick={() => this.props.onAddName(card, this.props.listType)} icon="fas fa-plus" text="Добавить" /></div>
                    : null}
                    {this.props.disabled ? null :
                    <div>
                        <ActionIcon className={"badge badge-" + (this.state.sorting ? "warning" : "secondary")} icon="fas fa-sort" onClick={this.setSorting} text="Сортировать" />
                    </div>}
                </div>
            </div>
        );
    }
}


export class PrayForList extends React.Component {

    render() {
        const list = this.props.list;
        const cols = 2;
        const decks = Math.floor(this.props.order.length / cols);
        let num = 1;
        let lt = [];
        for(let i=0; i<decks; ++i) {
            lt.push(
                <div className="card-deck" key={i}>
                    {this.props.order.slice(i*cols, i*cols+cols).map((id) =>
                        <PrayForCard
                            disabled={this.props.disabled}
                            key={id}
                            num={num++}
                            limit={this.props.limit}
                            card={list[id]}
                            listType={this.props.listType}
                            today={this.props.today}
                            onSort={this.props.onSort}
                            onRemove={this.props.onRemove}
                            onChangeHeader={this.props.onChangeHeader}
                            onChangeName={this.props.onChangeName}
                            onChangeTill={this.props.onChangeTill}
                            onAddName={this.props.onAddName}
                            onRemName={this.props.onRemName} />
                    )}
                </div>
            );
        }
        lt.push(
            <div className="card-deck" key={decks}>
                {this.props.order.slice(decks*cols).map((id) =>
                    <PrayForCard
                        disabled={this.props.disabled}
                        key={id}
                        num={num++}
                        limit={this.props.limit}
                        card={list[id]}
                        listType={this.props.listType}
                        today={this.props.today}
                        onSort={this.props.onSort}
                        onRemove={this.props.onRemove}
                        onChangeHeader={this.props.onChangeHeader}
                        onChangeName={this.props.onChangeName}
                        onChangeTill={this.props.onChangeTill}
                        onAddName={this.props.onAddName}
                        onRemName={this.props.onRemName} />
                )}
            </div>
        );
        return (
            <div>
                {lt}
                {this.props.disabled ? null :
                <p className="text-right"><ActionIcon onClick={() => this.props.onCreate(this.props.listType)} icon="far fa-plus-square" text="Создать группу" /></p>}
            </div>
        );
    }
}

