import React from 'react';

import {OnOff} from './components';
import {NameEdit, ListEdit, CollectionEdit} from './edit';
import {BIBLE_DEPTH, BookComponent, ChapterComponent, LineComponent} from './bible';
import loaded from './loader';


class _VolumeEditView extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
        }

        this.publicate = this.publicate.bind(this);
        this.changeName = this.changeName.bind(this);
    }

    changeName(name, cb) {
        $.ajax({
            url: URLS.VOLUME_EDIT,
            type: "POST",
            data: {
                id: this.props.volume.volume.id,
                action: "title",
                name: name
            },
            success: (res) => {
                if(cb) cb(res);
            },
            dataType: "json"
        });
    }

    publicate(on) {
        $.ajax({
            url: URLS.VOLUME_EDIT,
            type: "POST",
            data: {
                id: this.props.volume.volume.id,
                action: "public",
                on: on ? 1 : 0
            },
            success: (res) => {
                if(res.ok) {
                }
            },
            dataType: "json"
        });
    }

    render() {
        const data = this.props.volume;
        const volume = data.volume;
        const books = Object.values(this.props.books);
        return (
            <div>
                <dl className="row">
                    <dt className="col-sm-4">Название сборника</dt>
                    <dd className="col-sm-8">
                        <NameEdit remoteSave={this.changeName} name={volume.title} />
                    </dd>
                    <dt className="col-sm-4">Включенные книги</dt>
                    <dd className="col-sm-8">
                        <ListEdit
                            url={URLS.VOLUME_EDIT}
                            id={volume.id}
                            dialog="bibletree"
                            list={data.books}
                            component={BookComponent}
                            addValues={books}
                            itemKey="book_id"
                            addAction="add_book"
                            removeAction="rem_book" />
                    </dd>
                    <dt className="col-sm-4">Собрание глав</dt>
                    <dd className="col-sm-8">
                        <CollectionEdit
                            url={URLS.VOLUME_EDIT}
                            id={volume.id}
                            dialog="bibletree"
                            collection={data.ch_col}
                            component={ChapterComponent}
                            newAction="chapter"
                            deleteAction="del_chapter"
                            nameAction="title_chapter"
                            listKey="chapters"
                            addValues={books}
                            depth={BIBLE_DEPTH.CHAPTER}
                            itemKey="ch_id"
                            addAction="add_chapter"
                            removeAction="rem_chapter" />
                    </dd>
                </dl>
            </div>
        );
    }
}
export const VolumeEditView = loaded(_VolumeEditView, {volume: [URLS.VOLUME], books: [URLS.BOOKS]});

