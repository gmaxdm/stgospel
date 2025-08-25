import React from 'react';
import ReactDOM from 'react-dom';

import {GroupCreateView, GroupEditView} from './groups';
import {SynodikEditView} from './synodik';
import {VolumeEditView} from './volume';
import {MyPrayersEdit} from './profile';
import {TopicPosts} from './forum';
import {CalendarView} from './calendar';
import {clean} from './utils';


MODALDIALOG = document.getElementById("modaldialog");


const gc = document.getElementById("group-create");
if(gc) {
    ReactDOM.render(<GroupCreateView />, gc);
}


const ge = document.getElementById("group-edit");
if(ge) {
    ReactDOM.render(<GroupEditView />, ge);
}


const ve = document.getElementById("volume-edit");
if(ve) {
    ReactDOM.render(<VolumeEditView />, ve);
}


const pe = document.getElementById("myprayers-edit");
if(pe) {
    ReactDOM.render(<MyPrayersEdit />, pe);
}


const se = document.getElementById("synodik-edit");
if(se) {
    ReactDOM.render(<SynodikEditView />, se);
}


const calendar = document.getElementById("calendar-month");
if(calendar) {
    let month = 0,
        day = 0;
    if(/\/(\d+)\/(\d+)\/(\d+)/.test(window.location.href)) {
        const arr = /\/(\d+)\/(\d+)\/(\d+)/.exec(window.location.href);
        month = clean(arr[2]);
        day = clean(arr[3]);
    }
    ReactDOM.render(<CalendarView month={month} day={day}/>, calendar);
}


$(function() {
    $("body").on("click", ".top-messages li", function() {
        $(this).fadeOut();
    });
});

/* =========== FORUM ============ */
const ftopic = document.getElementById("topic-posts");
if(ftopic) {
    ReactDOM.render(
        <TopicPosts/>,
        ftopic
    );
}
