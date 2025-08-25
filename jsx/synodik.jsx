import React from 'react';

import {DialogIcon, Calendar, Accordion, AccordionCard,
        SpinnerInput} from './components';
import {NameEdit, ListEdit, PrayForCard,
        LIST_TYPE_NAME, init_lists, init_div} from './edit';
import loaded from './loader';


class _SynodikEditView extends React.Component {
    constructor(props) {
        super(props);

        this.today = getDate(props.data.date);
        this.rootDiv = init_div({
            id: props.data.root.id,
            name: props.data.root.name
        });
        props.data.synodik.forEach(it => {
            this.rootDiv[LIST_TYPE_NAME[it.list]].push({
                id: it.id,
                name: it.name,
                list: it.list,
                till: getDate(it.till),
                order: it.order
            });
        });
        this.state = {
            inaction: false,
        }

        this.post = this.post.bind(this);
        this.sortGroup = this.sortGroup.bind(this);
        this.changeName = this.changeName.bind(this);
        this.changeTill = this.changeTill.bind(this);
        this.addName = this.addName.bind(this);
        this.remName = this.remName.bind(this);
    }

    post(data, success) {
        $.ajax({
            url: URLS.SYNODIK_EDIT,
            type: "POST",
            data: data,
            success: success,
            dataType: "json"
        });
    }

    sortGroup(div, list, seria) {
        const listKey = LIST_TYPE_NAME[list];
        this.post({
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

    changeName(pf, name, cb) {
        this.post({
            pf_id: pf.id,
            action: "prayfor_name",
            name: name,
        }, (res) => {
            if(cb) cb(res);
        });
    }

    changeTill(pf, date) {
        this.post({
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
            action: "add_prayfor",
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

    render() {
        return (
            <div>
                <Accordion id="accordion">
                    <AccordionCard title="Список о здравии">
                        <PrayForCard
                            num={1}
                            limit={0}
                            card={this.rootDiv}
                            listType="H"
                            today={this.today}
                            onSort={this.sortGroup}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName} />
                    </AccordionCard>
                    <AccordionCard title="Список о болящих">
                        <PrayForCard
                            hint="Молитвы о болящих не будет использованы, если не добавлено ни одно имя"
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
                            hint="Молитвы о примирении враждующих не будет использованы, если не добавлено ни одно имя"
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
                        <PrayForCard
                            num={1}
                            limit={0}
                            card={this.rootDiv}
                            listType="R"
                            today={this.today}
                            onSort={this.sortGroup}
                            onChangeName={this.changeName}
                            onChangeTill={this.changeTill}
                            onAddName={this.addName}
                            onRemName={this.remName} />
                    </AccordionCard>
                </Accordion>
            </div>
        );
    }
}
export const SynodikEditView = loaded(_SynodikEditView, {data: [URLS.SYNODIK]});

