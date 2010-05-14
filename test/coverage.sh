#!/bin/sh
html_dir=`dirname $0`/cover
nosetests --with-coverage --cover-package=patu --cover-erase --cover-html --cover-html-dir=$html_dir "$@"
