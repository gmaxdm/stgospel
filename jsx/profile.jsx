import React from 'react';

import {ListEdit} from './edit';
import {PrayComponent} from './bible';
import loaded from './loader';


function _MyPrayersEdit(props) {
    return (
        <ListEdit
            url={URLS.MY_PRAYERS_EDIT}
            list={props.prays.prayers}
            component={PrayComponent}
            addValues={Object.values(props.all)}
            itemKey="pray_id"
            addAction="add_pray"
            removeAction="rem_pray" />
    );
}
export const MyPrayersEdit = loaded(_MyPrayersEdit, {prays: [URLS.MY_PRAYERS], all: [URLS.PRAYERS]});

