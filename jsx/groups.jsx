import React from 'react';

import {DialogIcon, Calendar, Accordion, AccordionCard,
        SpinnerInput} from './components';
import {NameEdit, ListEdit, PrayForCard, PrayForList,
        LIST_TYPE_NAME, init_lists, init_div} from './edit';
import {BookComponent, PrayComponent, Volume, QueueItemComponent} from './bible';
import loaded from './loader';


class _GroupCreateView extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            volume: 0
        }
        this.books = [];

        this.selectVolume = this.selectVolume.bind(this);
        this.changeBooks = this.changeBooks.bind(this);
    }

    selectVolume(e) {
        this.setState({volume: parseInt(e.target.value)});
    }

    changeBooks(books) {
        this.books = books;
    }

    render() {
        return (
            <dl className="row">
                <dt className="col-sm-5">Выберите сборник</dt>
                <dd className="col-sm-7">
                    <select name="volume" onChange={this.selectVolume}>
                        <option value="-1">--------</option>
                        {Object.values(this.props.volumes).map((vol) =>
                            <option key={vol.id} value={vol.id}>{vol.title}</option>
                        )}
                        {1 ? null :
                        <option value="0">Псалтирь на церковнославянском</option>
                        }
                    </select>
                </dd>
                <p className="p-3"><small className="text-muted">Возможно, вам потребуется вначале <a href={URLS.CREATE_VOLUME}>создать сборник</a>.</small></p>
                <dt className="col-sm-5">или</dt>
                <dd className="col-sm-7" />
                <dt className="col-sm-5">выберите одну или несколько книг</dt>
                <dd className="col-sm-7">
                    <ListEdit
                        dialog="bibletree"
                        disabled={!!this.state.volume}
                        itemKey="book_id"
                        onChange={this.changeBooks}
                        component={BookComponent}
                        addValues={Object.values(this.props.books)} />
                </dd>
                {1 ? null :
                <React.Fragment>
                <dt className="col-sm-5">Начало чтения</dt>
                <dd className="col-sm-7">{FORM_DATA.start_idx}</dd>
                <dt className="col-sm-5">
                    Количество глав в день<br />
                    <small className="text-muted">применимо только для собрания книг</small>
                </dt>
                <dd className="col-sm-7">
                    <input type="text" id="chpd" name="chpd" defaultValue={FORM_DATA.chpd} />
                </dd>
                <dt className="col-sm-5">
                    Количество имен в списке<br />
                    <small className="text-muted">0 - неограниченное количество</small>
                </dt>
                <dd className="col-sm-7">
                    <input type="text" id="names_cnt" name="names_cnt" defaultValue={FORM_DATA.names_cnt} />
                </dd>
                <dt className="col-sm-5"><label htmlFor="start">Дата начала чтения</label></dt>
                <dd className="col-sm-7">
                    <input type="text" id="start" name="start" defaultValue={FORM_DATA.start} required />
                </dd>
                <dt className="col-sm-5">
                    <label htmlFor="end">Дата завершения чтения</label><br />
                    <small className="text-muted">не заполняйте, если желаете читать неограниченное время</small>
                </dt>
                <dd className="col-sm-7">
                    <input type="text" id="end" name="end" defaultValue={FORM_DATA.end} />
                </dd>
                </React.Fragment>
                }
            </dl>
        );
    }
}
export const GroupCreateView = loaded(_GroupCreateView, {volumes: [URLS.VOLUMES], books: [URLS.BOOKS]});


class _GroupEditView extends React.Component {
    constructor(props) {
        super(props);
        const ids = {};
        this.divs = {};
        this.today = getDate(props.group.date);
        this.rootDiv = null;
        props.group.data.list.forEach((it) => {
            const div_id = String(it.id);
            let _div = null;
            if(it.root) {
                if(!this.rootDiv) {
                    this.rootDiv = init_div(it);
                }
                _div = this.rootDiv;
            } else {
                if(!this.divs[div_id]) {
                    this.divs[div_id] = init_div(it);
                    ids[div_id] = it.order;
                }
                _div = this.divs[div_id];
            }
            if(it.prayfor__id) {
                const pf = {
                    id: it.prayfor__id,
                    name: it.prayfor__name,
                    list: it.prayfor__list_type,
                    till: getDate(it.prayfor__till),
                    order: it.prayfor__order,
                };
                _div[LIST_TYPE_NAME[pf.list]].push(pf);
            }
        });
        this.volume = new Volume(props.group.data.volume);
        this.queue = this.volume.queue(props.group.data.settings.chpd);
        let start_id = props.group.data.settings.start_idx-1;
        if(this.queue[start_id] === undefined) {
            start_id = 0;
        }
        this.state = {
            inaction: false,
            ids: Object.keys(ids).sort((a, b) => ids[a] - ids[b]),
            start_id: start_id,
            chpd: props.group.data.settings.chpd,
            ncnt: props.group.data.settings.ncnt,
            start_date: getDate(props.group.data.settings.start),
            end_date: getDate(props.group.data.settings.end),
            bdate_date: getDate(props.group.data.settings.bdate),
            lorder: props.group.data.settings.lorder,
        }

        this.post = this.post.bind(this);
        this.changeStartIdx = this.changeStartIdx.bind(this);
        this.changeNamesCnt = this.changeNamesCnt.bind(this);
        this.changeChpd = this.changeChpd.bind(this);
        this.changeGroupName = this.changeGroupName.bind(this);
        this.changeDate = this.changeDate.bind(this);
        this.sortGroup = this.sortGroup.bind(this);
        this.newGroup = this.newGroup.bind(this);
        this.removeGroup = this.removeGroup.bind(this);
        this.changeDivName = this.changeDivName.bind(this);
        this.changeName = this.changeName.bind(this);
        this.changeTill = this.changeTill.bind(this);
        this.addName = this.addName.bind(this);
        this.remName = this.remName.bind(this);
        this.changeListOrder = this.changeListOrder.bind(this);
        this.isBreakDate = this.isBreakDate.bind(this);
    }

    isBreakDate() {
        return this.state.bdate_date && this.state.end_date && this.state.bdate_date > this.state.end_date;
    }

    post(data, success) {
        $.ajax({
            url: URLS.GROUP_EDIT,
            type: "POST",
            data: data,
            success: success,
            dataType: "json"
        });
    }

    changeStartIdx(idx) {
        this.post({
            id: this.props.group.data.group.id,
            action: "startidx",
            idx: idx,
        }, (res) => {
            this.setState({start_id: idx-1});
        });
    }

    changeNamesCnt(cnt) {
        this.post({
            id: this.props.group.data.group.id,
            action: "namescnt",
            cnt: cnt,
        }, (res) => {
            this.setState({ncnt: cnt});
        });
    }

    changeChpd(cnt) {
        this.post({
            id: this.props.group.data.group.id,
            action: "chpd",
            chpd: cnt,
        }, (res) => {
            this.queue = this.volume.queue(cnt);
            this.setState((pS) => {
                const ln = this.queue.length;
                let _sid = pS.start_id
                if(ln < pS.start_id) _sid = ln - 1;
                return {chpd: cnt, start_id: _sid};
            });
        });
    }

    changeDate(date, name) {
        this.startDateDialog.close();
        this.endDateDialog.close();
        this.breakDateDialog && this.breakDateDialog.close();
        const key = name + "_date";
        const iso_dt = iso_date(date);
        if(iso_date(this.state[key]) === iso_dt) return;
        this.post({
            id: this.props.group.data.group.id,
            action: "date",
            name: name,
            date: iso_dt,
        }, (res) => {
            const _st = {};
            _st[key] = date;
            this.setState(_st);
        });
    }

    changeGroupName(name, cb) {
        this.post({
            id: this.props.group.data.group.id,
            action: "title",
            name: name,
        }, (res) => {
            if(cb) cb(res);
        });
    }

    newGroup(list) {
        const order = Object.keys(this.divs).length;
        this.post({
            id: this.props.group.data.group.id,
            order: order,
            list: list,
            action: "add_div",
        }, (res) => {
            if(!res.ok) {
                raise_error("Не удается создать группу.");
                return;
            }
            const div_id = String(res.ok.div);
            this.divs[div_id] = {
                id: div_id,
                name: null,
                order: order
            };
            Object.assign(this.divs[div_id], init_lists());
            this.divs[div_id][LIST_TYPE_NAME[list]].push({
                id: res.ok.pf,
                name: "",
                list: list,
                till: null,
            });
            this.setState((pS) => ({
                ids: pS.ids.concat([div_id])
            }));
        });
    }

    sortGroup(div, list, seria) {
        const listKey = LIST_TYPE_NAME[list];
        this.post({
            id: this.props.group.data.group.id,
            div_id: div.id,
            list: list,
            action: "sort_div",
            seria: seria.join(','),
        }, (res) => {
            if(res.ok) {
                let nl = [];
                seria.forEach((i) => {
                    nl.push(div[listKey][i-1]);
                });
                div[listKey] = nl;
                this.setState({inaction: false});
            }
        });
    }

    removeGroup(div) {
        if(!confirm("Вы действительно хотите удалить группу со списком?\nВнимание! Удалится вся группа: и о здравии и об упокоении!")) return;
        this.post({
            id: this.props.group.data.group.id,
            div_id: div.id,
            action: "del_div",
        }, (res) => {
            if(!res.ok) {
                raise_error("Не удается удалить группу.");
                return;
            }
            const div_id = String(div.id);
            delete this.divs[div_id];
            this.setState((pS) => {
                const id = pS.ids.indexOf(div_id);
                pS.ids.splice(id, 1);
                return {ids: pS.ids};
            });
        });
    }

    changeDivName(div, name, cb) {
        this.post({
            id: this.props.group.data.group.id,
            div_id: div.id,
            action: "div_name",
            name: name,
        }, (res) => {
            if(cb) cb(res);
        });
    }

    changeName(pf, name, cb) {
        this.post({
            id: this.props.group.data.group.id,
            pf_id: pf.id,
            action: "prayfor_name",
            name: name,
        }, (res) => {
            if(cb) cb(res);
        });
    }

    changeTill(pf, date) {
        this.post({
            id: this.props.group.data.group.id,
            pf_id: pf.id,
            action: "prayfor_till",
            till: iso_date(date),
        }, (res) => {
            if(res.ok) {
                pf.till = date;
                this.setState({inaction: false});
            }
        });
    }

    addName(div, list) {
        const listKey = LIST_TYPE_NAME[list];
        const order = div[listKey].length;
        this.post({
            id: this.props.group.data.group.id,
            action: "add_prayfor",
            div_id: div.id,
            list: list,
            order: order,
        }, (res) => {
            if(res.ok) {
                div[listKey].push({
                    id: res.ok,
                    name: "",
                    list: list,
                    till: null,
                    order: order,
                });
                this.setState({inaction: false});
            }
        });
    }

    remName(div, pf, i, listKey, title) {
        if(!confirm("Вы действительно хотите " + title + "?")) return;
        this.post({
            id: this.props.group.data.group.id,
            pf_id: pf.id,
            action: "rem_prayfor",
        }, (res) => {
            if(res.ok) {
                const lt = div[listKey];
                lt.splice(i, 1);
                this.setState({inaction: false});
            }
        });
    }

    changeListOrder(ch) {
        this.post({
            id: this.props.group.data.group.id,
            action: "listorder",
            ch: ch
        }, (res) => {
            if(res.ok) {
                this.setState({lorder: ch});
            }
        });
    }

    render() {
        const noLimit = "не ограничено";
        const data = this.props.group.data;
        const group = this.props.group.data.group;
        const volume = this.props.group.data.volume;
        const settings = this.props.group.data.settings;
        const prays = this.props.prays;
        let start_prays = [];
        let end_prays = [];
        data.prays.forEach((pr) => {
            if(pr.start) {
                start_prays.push(pr);
            }
            if(pr.end) {
                end_prays.push(pr);
            }
        });
        start_prays = start_prays.sort((a, b) => a.order - b.order);
        end_prays = end_prays.sort((a, b) => a.order - b.order);
        let endDefaultDate = this.state.start_date.addDays(this.queue.length-1);
        if(endDefaultDate < this.today) {
            endDefaultDate = this.today;
        }
        return (
            <div>
                <dl className="row">
                    <dt className="col-sm-5">Название чтения</dt>
                    <dd className="col-sm-7">
                        <NameEdit remoteSave={this.changeGroupName} name={group.name} disabled={!this.props.group.group_user.edit} />
                    </dd>
                    <dt className="col-sm-5">Сборник</dt>
                    <dd className="col-sm-7">
                        <strong>{volume.volume.title}</strong>
                    </dd>
                </dl>
                <Accordion id="accordion">
                    <AccordionCard title="Молитвы в начале">
                        <ListEdit
                            disabled={!this.props.group.group_user.edit}
                            url={URLS.GROUP_EDIT}
                            id={group.id}
                            list={start_prays}
                            component={PrayComponent}
                            addValues={Object.values(prays)}
                            itemKey="pray_id"
                            sortAction="sort_start_pray"
                            addAction="add_start_pray"
                            removeAction="rem_pray" />
                    </AccordionCard>
                    <AccordionCard title="Прошения для молитвы по соглашению">
                        <PrayForCard
                            disabled={!this.props.group.group_user.edit}
                            hint="Молитва по соглашению не будет использована в чтении, если не добавлено ни одно прошение. Добавляйте прошения в предложном падеже, например, о болящих, о мире и т.д."
                            names={["прошение", "прошения"]}
                            num={1}
                            limit={0}
                            card={this.rootDiv}
                            listType="P"
                            today={this.today}
                            onSort={this.sortGroup}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName} />
                    </AccordionCard>
                    <AccordionCard title="Список о здравии">
                        <PrayForList
                            disabled={!this.props.group.group_user.edit}
                            list={this.divs}
                            today={this.today}
                            order={this.state.ids}
                            onCreate={this.newGroup}
                            onSort={this.sortGroup}
                            onRemove={this.removeGroup}
                            onChangeHeader={this.changeDivName}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName}
                            limit={this.state.ncnt}
                            listType="H" />
                    </AccordionCard>
                    <AccordionCard title="Список о болящих">
                        <PrayForCard
                            disabled={!this.props.group.group_user.edit}
                            hint="Молитвы о болящих не будет использованы в чтении, если не добавлено ни одно имя"
                            num={1}
                            limit={0}
                            card={this.rootDiv}
                            listType="S"
                            today={this.today}
                            onSort={this.sortGroup}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName} />
                    </AccordionCard>
                    <AccordionCard title="Список о примирении враждующих">
                        <PrayForCard
                            disabled={!this.props.group.group_user.edit}
                            hint="Молитвы о примирении враждующих не будет использованы в чтении, если не добавлено ни одно имя"
                            num={1}
                            limit={0}
                            card={this.rootDiv}
                            listType="W"
                            today={this.today}
                            onSort={this.sortGroup}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName} />
                    </AccordionCard>
                    <AccordionCard title="Список о воинах">
                        <PrayForCard
                            disabled={!this.props.group.group_user.edit}
                            hint={<span>Молитва о воинах не будет использована, если не добавлено ни одно имя.<br/>Добавте имена в винительном падеже (кого?)</span>}
                            num={1}
                            limit={0}
                            card={this.rootDiv}
                            listType="A"
                            today={this.today}
                            onSort={this.sortGroup}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName} />
                    </AccordionCard>
                    <AccordionCard title="Список об упокоении">
                        <PrayForList
                            disabled={!this.props.group.group_user.edit}
                            list={this.divs}
                            today={this.today}
                            order={this.state.ids}
                            onCreate={this.newGroup}
                            onSort={this.sortGroup}
                            onRemove={this.removeGroup}
                            onChangeHeader={this.changeDivName}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName}
                            limit={this.state.ncnt}
                            listType="R"/>
                    </AccordionCard>
                    <AccordionCard title="Молитвы в конце">
                        <ListEdit
                            disabled={!this.props.group.group_user.edit}
                            url={URLS.GROUP_EDIT}
                            id={group.id}
                            list={end_prays}
                            component={PrayComponent}
                            addValues={Object.values(prays)}
                            itemKey="pray_id"
                            sortAction="sort_end_pray"
                            addAction="add_end_pray"
                            removeAction="rem_pray" />
                    </AccordionCard>
                </Accordion>
                <h4 className="mt-4">Основные настройки</h4>
                <dl className="row">
                    <dt className="col-sm-5 mb-4">Начало чтения</dt>
                    <dd className="col-sm-7">
                        <ListEdit
                            disabled={!this.props.group.group_user.admin}
                            single
                            onChange={(qi) => this.changeStartIdx(qi.id)}
                            list={[this.queue[this.state.start_id]]}
                            component={QueueItemComponent}
                            addValues={this.queue} />
                    </dd>
                    {volume.books.length ?
                        <React.Fragment>
                            <dt className="col-sm-5 mb-4">Количество глав в день<br /><small className="text-muted">применимо только для собрания книг</small></dt>
                            <dd className="col-sm-7">
                                {this.props.group.group_user.admin ?
                                <SpinnerInput name="chpd" onChange={this.changeChpd} defaultValue={settings.chpd} min={1} max={5} />
                                : <span>{settings.chpd}</span>}
                            </dd>
                        </React.Fragment>
                    : null}
                    <dt className="col-sm-5 mb-4">
                        Количество имен в списке
                        {this.props.group.group_user.admin ?
                        <React.Fragment><br/><small className="text-muted">0 - неограниченное количество</small></React.Fragment>
                        : null}
                    </dt>
                    <dd className="col-sm-7">
                        {this.props.group.group_user.admin ?
                        <SpinnerInput name="ncnt" onChange={this.changeNamesCnt} defaultValue={settings.ncnt} min={0} max={5} />
                        : <span>{settings.ncnt || noLimit}</span>}
                    </dd>
                    <dt className="col-sm-5 mb-4">Дата начала чтения</dt>
                    <dd className="col-sm-7">
                        {rus_date(this.state.start_date)}&nbsp;
                        {this.props.group.group_user.admin ?
                        <DialogIcon
                            ref={d => this.startDateDialog = d}
                            title="изменить дату"
                            icon="far fa-calendar-alt"
                            inner={<Calendar defaultValue={this.state.start_date} onSelect={(date) => this.changeDate(date, "start")} />} />
                        : null}
                    </dd>
                    <dt className="col-sm-5 mb-4">
                        Дата завершения чтения<br/>
                        {this.props.group.group_user.admin ?
                            <small className="text-muted">в этот день чтение еще есть</small>
                        : null}
                    </dt>
                    <dd className="col-sm-7">
                        {this.state.end_date ? rus_date(this.state.end_date) : noLimit}&nbsp;
                        {this.props.group.group_user.admin ?
                        <DialogIcon
                            ref={d => this.endDateDialog = d}
                            title="изменить дату"
                            icon="far fa-calendar-alt"
                            inner={<Calendar nullable defaultValue={endDefaultDate} onSelect={(date) => this.changeDate(date, "end")} />} />
                        : null}
                    </dd>
                    {this.state.end_date ?
                    <React.Fragment>
                    <dt className="col-sm-5 mb-4">
                        Дата возобновления чтения
                        {this.props.group.group_user.admin ?
                        <React.Fragment>
                        <br/><small className="text-muted">если определена дата завершения чтения, то, установив эту дату, вы определите перерыв в чтении. В этот день чтение продолжится неограничено, пока вы не удалите эту дату и не определите новую дату завершения чтения.</small>
                        </React.Fragment>
                        : null}
                    </dt>
                    <dd className="col-sm-7">
                        {this.isBreakDate() ? rus_date(this.state.bdate_date) : "не назначена"}&nbsp;
                        {this.props.group.group_user.admin ?
                        <DialogIcon
                            ref={d => this.breakDateDialog = d}
                            title="изменить дату"
                            icon="far fa-calendar-alt"
                            inner={<Calendar nullable defaultValue={this.state.end_date.addDays(7)} onSelect={(date) => this.changeDate(date, "bdate")} />} />
                        : null}
                    </dd>
                    </React.Fragment>
                    : null}
                    <dt className="col-sm-5 mb-4">Списки поминовений</dt>
                    <dd className="col-sm-7">
                        <input id="rl-b" type="radio" name="rlist" disabled={!this.props.group.group_user.admin} checked={this.state.lorder === "B"} value="B" onChange={() => this.changeListOrder("B")}/> <label htmlFor="rl-b">между главами</label><br />
                        <small className="text-muted">списки о здравии (а также о болящих, о враждующих и т.д., если они есть) будут следовать за первой главой, список об упокоении - за второй, потом все оставшиеся главы текущего чтения</small><br />
                        <input id="rl-a" type="radio" name="rlist" disabled={!this.props.group.group_user.admin} checked={this.state.lorder === "A"} value="A" onChange={() => this.changeListOrder("A")}/> <label htmlFor="rl-a">в конце всего чтения</label><br />
                        <small className="text-muted">все списки о здравии и об упокоении будет следовать за всеми главами текущего чтения</small>
                    </dd>
                </dl>
            </div>
        );
    }
}
export const GroupEditView = loaded(_GroupEditView, {group: [URLS.GROUP], prays: [URLS.PRAYERS]});

