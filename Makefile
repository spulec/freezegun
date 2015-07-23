SHELL := /bin/bash

init:
	python setup.py develop
	pip install -r requirements.txt

test:
	rm -f .coverage
	nosetests $(NOSE_ARGS) ./tests/

travis:
	nosetests --with-coverage ./tests/

tdaemon:
	tdaemon -t nose ./tests/ --custom-args="--with-growl"

publish:
	python setup.py sdist bdist_wheel upload
