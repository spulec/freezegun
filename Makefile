SHELL := /bin/bash

init:
	python setup.py develop
	pip install -r requirements.txt

test:
	rm -f .coverage
	pytest

travis:
	pytest --cov

tdaemon:
	tdaemon -t nose ./tests/ --custom-args="--with-growl"

publish:
	rm -rf dist
	python setup.py sdist bdist_wheel
	twine upload dist/*

venv:
	virtualenv venv
	venv/bin/pip install -r requirements.txt
