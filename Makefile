SHELL := /bin/bash

init:
	python setup.py develop
	pip install -r requirements.txt

test:
	rm -f .coverage
	nosetests --with-coverage ./tests/

travis:
	nosetests --with-coverage ./tests/

tdaemon:
	tdaemon -t nose ./tests/ --custom-args="--with-growl"