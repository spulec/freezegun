SHELL := /bin/bash

init:
	python setup.py develop
	pip install -r requirements.txt

test:
	nosetests ./tests/

travis:
	nosetests ./tests/

tdaemon:
	tdaemon -t nose ./tests/ --custom-args="--with-growl"