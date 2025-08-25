import React from 'react';
import ReactDOM from 'react-dom';


class Dialog extends React.Component {
    render() {
        return (
            <div className="dialog__main" onClick={this.props.onClose}>
                <div className="dialog__close" onClick={this.props.onClose}>закрыть</div>
                <div className="dialog" onClick={(e) => e.stopPropagation()}>
                    {this.props.children}
                </div>
            </div>
        );
    }
}


export function contextDialog(Component) {
    return class extends React.Component {
        constructor(props) {
            super(props);
            this.state = {
                visible: false,
            };
            this.cont = null;
            this.onClose = null;

            this.create = this.create.bind(this);
            this.close = this.close.bind(this);
        }

        create(Elements) {
            this.cont = ReactDOM.createPortal(<Dialog onClose={this.close}>{Elements}</Dialog>, MODALDIALOG);
            this.setState({visible: true});
        }

        close() {
            this.setState({visible: false},
                () => {
                    this.cont = null;
                    if(is_function(this.onClose)) {
                        this.onClose();
                    }
                }
            );
        }

        render() {
            return (
                <React.Fragment>
                    {this.state.visible ? this.cont : null}
                    <Component dialog={this} {...this.props} />
                </React.Fragment>
            );
        }
    }
}


export function hideModalDialog() {
    MODALDIALOG.classList.add("hidden");
}


export function showModalDialog(Component) {
    ReactDOM.render(<Dialog onClose={hideModalDialog}>{Component}</Dialog>, MODALDIALOG);
    MODALDIALOG.classList.remove("hidden");
}

