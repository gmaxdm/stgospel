import React from 'react';

import {contextDialog} from './modaldialog';


export const ActionIcon = ({className, disabled, title, onClick, text, icon}) => {
    const cls = (className || "") + (disabled ? " text-muted" : "");
    return (
        <a href="#" className={cls} title={title} onClick={(e) => {e.preventDefault(); if(disabled) return; onClick(e);}}>
            <i className={icon} />{text ? " " : null}{text}
        </a>
    );
}


class _DialogIcon extends React.Component {
    constructor(props) {
        super(props);
        this.dialog = props.dialog;
        this.dialog.onClose = props.onClose;

        this.showDialog = this.showDialog.bind(this);
    }

    showDialog() {
        this.dialog.create(this.props.inner);
    }

    render() {
        return (
            <ActionIcon disabled={this.props.disabled} onClick={this.showDialog} title={this.props.title} icon={this.props.icon} text={this.props.text} />
        );
    }
}
export const DialogIcon = contextDialog(_DialogIcon);


export class Calendar extends React.Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        this.$calendar = $(this.div);
        this.$calendar.datepicker({
            dateFormat: DATE_FORMAT,
            defaultDate: this.props.defaultValue,
            showButtonPanel: true,
            currentText: "Сегодня",
            closeText: "Готово",
        });
    }

    render() {
        return (
            <div className="container">
                <p className="text-right">
                    {this.props.nullable ?
                    <ActionIcon onClick={() => this.props.onSelect()} title="сбросить дату" icon="far fa-calendar-minus" />
                    : null}
                    &nbsp;
                    <ActionIcon onClick={() => this.props.onSelect(this.$calendar.datepicker("getDate"))} icon="fas fa-check-circle" />
                </p>
                <div className="row justify-content-center">
                    <div className="" ref={e => this.div = e} />
                </div>
            </div>
        );
    }
}


export class SpinnerInput extends React.Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        this.$spinner = $(this.input);
        this.$spinner.spinner({
            min: this.props.min,
            max: this.props.max,
            change: (e, ui) => this.props.onChange(+e.target.value),
        });
    }

    render() {
        return (
            <input name={this.props.name} min={this.props.min} max={this.props.max} defaultValue={this.props.defaultValue} ref={e => this.input = e} type="number" />
        );
    }
}


export class DefaultComponent extends React.Component {
    render() {
        return (
            <span>{JSON.stringify(this.props.data)}</span>
        );
    }
}


export class MultiList extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selected: {},
        }
        this.values = props.values;

        this.select = this.select.bind(this);
        this.ok = this.ok.bind(this);
    }

    select(val) {
        if(this.props.single) {
            const _sel = {};
            _sel[val.id] = val;
            this.setState({
                selected: _sel
            });
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

    ok() {
        this.props.onSelect(this.state.selected);
    }

    render() {
        const Component = this.props.component || DefaultComponent;
        return (
            <React.Fragment>
                <p className="text-right"><ActionIcon onClick={this.ok} disabled={!Object.keys(this.state.selected).length} icon="fas fa-check-circle" /></p>
                <ul className="list-unstyled select__items">
                    {this.values.map((val, i) =>
                        <li key={i} onClick={(e) => this.select(val)} className={this.state.selected[val.id] ? "selected" : ""}><Component data={val} /></li>
                    )}
                </ul>
            </React.Fragment>
        );
    }
}

    
export class OnOff extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            on: props.on
        }

        this.toggle = this.toggle.bind(this);
    }

    toggle() {
        this.setState((pS) => ({
            on: !pS.on
        }), () => {
            this.props.onChange(this.state.on);
        });
    }

    render() {
        return (
            <div className="onoff">
                <input type="checkbox" defaultChecked={this.state.on} name="toggle" id={this.props.id} />
                <label htmlFor={this.props.id} className={this.state.on ? "toggled": ""} onClick={this.toggle}>Нет</label>
            </div>
        );
    }
}


export class AccordionCard extends React.Component {
    render() {
        return (
            <div className="card">
                <div className="card-header" id={this.props.headerId}>
                    <h5 className="mb-0">
                        <button className="btn btn-link collapsed" data-toggle="collapse" data-target={"#"+this.props.bodyId} aria-expanded="true" aria-controls={this.props.bodyId}>
                            {this.props.title}
                        </button>
                    </h5>
                </div>
                <div id={this.props.bodyId} className="collapse" aria-labelledby={this.props.headerId} data-parent={"#"+this.props.parent}>
                    <div className="card-body">
                        {this.props.children}
                    </div>
                </div>
            </div>
        );
    }
}


export class Accordion extends React.Component {
    render() {
        const id = this.props.id;
        return (
            <div id={id}>
                {React.Children.map(this.props.children, (ac, i) => {
                    return React.cloneElement(ac, {
                        headerId: id + "_h_" + i,
                        bodyId: id + "_b_" + i,
                        parent: id,
                    });
                })}
            </div>
        );
    }
}

