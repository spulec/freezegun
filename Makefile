SHELL := /bin/bash

init:
	python setup.py develop
	pip install -r requirements.txt

test:
	rm -f .coverage
	pytest

tag:
	python create_tag.py

publish:
	rm -rf dist
	python -m build
	twine upload dist/*

venv:
	virtualenv venv
	venv/bin/pip install -r requirements.txt
