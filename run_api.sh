#!/bin/bash

scriptname=`basename "$0"`


if [ -f api.pid ];then
  pid=$(cat api.pid)
  echo "killing api $pid"
  kill $pid
  rm api.pid
else
	echo "running $scriptname"
	nohup gunicorn --timeout 120 --bind 0.0.0.0:5000 api:app > api.log & echo $! > api.pid
fi