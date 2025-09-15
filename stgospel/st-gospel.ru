upstream stgospel {
    server unix:/home/www/logs/st-gospel/uwsgi/st-gospel.sock;
}

server {
     listen 80;
     server_name st-gospel.ru www.st-gospel.ru;
     rewrite ^ https://st-gospel.ru$request_uri? permanent;
}

server {
     listen 443 ssl;
     server_name www.st-gospel.ru;
     keepalive_timeout   70;
     ssl_certificate     /home/www/ssl/st-gospel.ru.chained.crt;
     ssl_certificate_key /home/www/ssl/st-gospel.ru.key;
     rewrite ^ https://st-gospel.ru$request_uri? permanent;
}

server {
    #listen 80 default_server;
    #listen [::]:80 default_server;
    listen 443 ssl;
    server_name st-gospel.ru;
    keepalive_timeout   70;

    if ($badagent) {
        return 403;
    }

    ssl_certificate     /home/www/ssl/st-gospel.ru.chained.crt;
    ssl_certificate_key /home/www/ssl/st-gospel.ru.key;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;

    #ssl_ciphers 'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS:!3DES';
    #ssl_ciphers HIGH+kEECDH+AESGCM:HIGH+kEECDH:HIGH+kEDH:HIGH:!aNULL;

    #ssl_prefer_server_ciphers on;

    #add_header X-Content-Type-Options nosniff;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 5m;

    access_log  /home/www/logs/st-gospel/nginx/access.log;
    error_log  /home/www/logs/st-gospel/nginx/error.log; 

    location /favicon.ico {
        root /home/www/stgospel/root;
    }

    location /robots.txt {
        root /home/www/stgospel/root;
    }

    location /sitemap.xml {
        root /home/www/stgospel/root;
    }

    location /manifest.json {
        root /home/www/stgospel/root;
    }

    location /static/ {
        access_log off;
        root /home/www/static/st-gospel;
        expires max;
    }

    location /media/ {
        access_log off;
        root /home/www/media/st-gospel;
        expires max;
    }

    location / {
        proxy_set_header HTTP_X_FORWARDED_FOR $http_x_forwarded_for;
        uwsgi_pass  stgospel;
        include     uwsgi_params;
    }

    #location /.well-known/pki-validation/570D5DC33184944885996F9A85DC07E8.txt {
    #    root /home/www/stgospel;
    #}
}
