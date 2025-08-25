import React, {useState, useRef} from 'react';
import { Editor } from '@tinymce/tinymce-react';

import loaded from './loader';
import {decode64, post, clone} from './utils';
import {POST_LIKE_URL, POST_DEL_URL, POST_EDIT_URL,
        FORUM_TOPIC_POSTS_URL, UPLOAD_IMG_URL} from './models/urls';


const imageUploadHandler = (blobInfo, success, failure) => {
    if (blobInfo.blob().size > 1024 * 1024) {
        return failure(T.FIB, {remove: true});
    }
    const formData = new FormData();
    formData.append('img', blobInfo.blob(), blobInfo.filename());
    $.ajax({
        url: UPLOAD_IMG_URL,
        type: "post",
        contentType: false,
        processData: false,
        data: formData,
        success: function(data) {
            success(data.location);
        },
        error: function(jqXHR, status, error) {
            failure('HTTP Error: ' + status + ": " + error, {remove: true});
        }
     });
};


const TMCE = {
    height: 300,
    selector: "textarea",
    plugins: "insertdatetime table lists link charmap emoticons image",
    language: LANG,
    toolbar: 'styles | bold italic | alignleft aligncenter alignright alignjustify | link | numlist bullist outdent indent | image emoticons',
    lists_indent_on_tab: false,
    images_upload_handler: imageUploadHandler,
    convert_urls : false,
    branding: false,
    promotion: false
};


function _TopicPosts({data}) {
    const [posts, setPosts] = useState({});
    const [edit, setEdit] = useState(0);

    const editRef = useRef(null);
    const newRef = useRef(null);

    // get state posts as prio values
    // and extend them with data.posts
    const _posts = clone(posts);
    data.posts.forEach(p => {
        if(!_posts[p.id]) {
            _posts[p.id] = p;
        }
    });

    const likeCl = (e, pid) => {
        e.preventDefault();
        if(!data.ro) {
            post(POST_LIKE_URL, {post: pid}, (res) => {
                if(res && res.em) {
                    const _p = _posts[pid];
                    _p.emotion = res.em;
                    _p.like = res.likes;
                    posts[pid] = _p;
                    setPosts(clone(posts));
                }
            });
        }
    };
    const delCl = (e, pid) => {
        e.preventDefault();
        if(!data.ro) {
            if(confirm(T.FPD)) {
                post(POST_DEL_URL, {post: pid}, (res) => {
                    if(res && res.ok) {
                        const _p = _posts[pid];
                        _p.del = 1;
                        _p.ce = 0;
                        posts[pid] = _p;
                        setPosts(clone(posts));
                    }
                });
            }
        }
    };
    const editCl = (e, p) => {
        e.preventDefault();
        if(!data.ro) {
            const d = {
                t: TOPIC_ID
            };
            let editor = newRef.current;
            if(p) {
                // edit post
                d.post = p.id;
                editor = editRef.current;
            }
            d.msg = editor.getContent();
            if(d.msg) {
                post(POST_EDIT_URL, d, (res) => {
                    if(res && res.post) {
                        let _p = res.post;
                        if(p) {
                            _p = _posts[p.id];
                            _p.msg = res.post.msg;
                            _p.edit = res.post.edit;
                            _p.mod = res.post.mod;
                        }
                        posts[_p.id] = _p;
                        setPosts(clone(posts));
                        setEdit(0);
                    } else {
                        console.log(res);
                    }
                    editor.setContent('');
                });
            }
        }
    };
    return (
        <>{Object.values(_posts).sort((a, b) => a.id > b.id).map(p =>
            <div key={p.id} className="p-2 mt-4">
                <div className="clearfix">
                    <div className="float-left">
                        <span className="user-name">{p.user}</span>
                        <span className="post-date">{p.cdate}</span>
                        {p.edit ? <span className="text-muted pl-1"><small><em>{T.FED}</em></small></span> : null}
                        {p.mod ? null : <span className="post-mod">{T.FMOD}</span>}
                    </div>
                    <div className="float-right">
                        <button className={"post-like i32_" + (p.emotion == "L" ? 2 : 1)} onClick={e => likeCl(e, p.id)}><span>{p.like}</span></button>
                    </div>
                </div>
                {p.del ?
                    <div className="post-message small text-muted">
                        <em>{T.FPDM}</em>
                    </div>
                    : p.id === edit ? 
                    <div className="mb-2">
                        <Editor tinymceScriptSrc={TINYMCE_URL} onInit={(e, editor) => editRef.current = editor} initialValue={decode64(p.msg)} init={TMCE} />
                    </div>
                    :
                    <div className="post-message" dangerouslySetInnerHTML={{__html: decode64(p.msg)}} />
                }
                {p.id === edit ?
                <div className="post-actions text-right">
                    <button className="btn btn-secondary mr-1" onClick={e => setEdit(0)}>{T.FC}</button>
                    <button className="btn btn-primary" onClick={e => editCl(e, p)}>{T.FE}</button>
                </div>
                : p.ce ?
                <div className="post-actions text-right">
                    <button className="mr-2 btn btn-danger" onClick={e => delCl(e, p.id)}>{T.FD}</button>
                    <button className="btn btn-primary" onClick={e => setEdit(p.id)}>{T.FE}</button>
                </div>
                : null}
            </div>
        )}
        {data.ro ? null :
        <div className="">
            <dl className="new-forum-post">
                <dt>{T.FP}</dt>
                <dd><Editor tinymceScriptSrc={TINYMCE_URL} onInit={(e, editor) => newRef.current = editor} initialValue="" init={TMCE} /></dd>
            </dl>
            <div className="text-right p-1"><button className="btn btn-success btn-post-edit" onClick={editCl}>{T.FS}</button></div>
        </div>}
        </>
    );
}
export const TopicPosts = loaded(_TopicPosts, {data: [FORUM_TOPIC_POSTS_URL, {t: TOPIC_ID}]});

