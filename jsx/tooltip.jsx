import React from 'react';


export function TooltipY(props) {
    return (
        <div className={"tooltipY " + (props.className || "")} data-direction={props.dir}>
            <div className={"tooltipY__initiator " + (props.initiatorClass || "")}>{props.initiator || null}</div>
            <div className={"tooltipY__item " + (props.itemClass || "")}>
                {props.children}
            </div>
        </div>
    );
}

