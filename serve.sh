#!/usr/bin/env bash

cd `dirname $0`
exec ./run.sh paster serve --reload development.ini

