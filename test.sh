#!/bin/sh
nosetests --with-coverage --cover-package=patu --cover-erase "$@"
