ID=$(cat $HOME/logs/st-gospel/uwsgi/st-gospel.pid)
echo "process id=$ID"
if [ -n "$ID" ]; then
    kill -INT $ID
    sleep 5
    uwsgi --ini stgospel/wsgi.ini
    echo "restarted"
    exit 0
fi
ps aux | grep gospel
echo "process not found"
