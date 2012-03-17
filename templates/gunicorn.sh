#!/bin/sh

# Usage: ./gunicorn.sh { start | stop | restart }

GUNICORN="/home/$USER/bin/gunicorn_django"
DIR="$( cd "$( dirname "$0" )" && pwd )"
BASE_CMD="$GUNICORN -c $DIR/config.py"
SERVER_PID="$DIR/wsgi.pid "

start_server () {
  if [ -f $1 ]; then
    if [ "$(ps -p `cat $1` | wc -l)" -gt 1 ]; then
       echo "A server is already running"
       return
    fi
  fi
  cd $DIR
  echo "starting $BASE_CMD --daemon --pid=$1"
  $BASE_CMD --daemon --pid=$1
}

stop_server (){
  if [ -f $1 ] && [ "$(ps -p `cat $1` | wc -l)" -gt 1 ]; then
    echo "stopping server"
    kill -9 `cat $1`
    rm $1
  else
    if [ -f $1 ]; then
      echo "server not running"
    else
      echo "No pid file found for server"
    fi
  fi
}

case "$1" in
'start')
  start_server $SERVER_PID
  ;;
'stop')
  stop_server $SERVER_PID
  ;;
'restart')
  stop_server $SERVER_PID
  sleep 7
  start_server $SERVER_PID
  ;;
*)
  echo "Usage: $0 { start | stop | restart }"
  ;;
esac

exit 0