SHELL := /bin/bash

init:
	python -m pip install -e develop
	pip install -r requirements.txt

test:
	rm -f .coverage
	pytest

tag:
	python create_tag.py

publish:
	rm -rf dist
	python -m pep517.build --source --binary .
	twine upload dist/*

venv:
	virtualenv venv
	venv/bin/pip install -r requirements.txt
