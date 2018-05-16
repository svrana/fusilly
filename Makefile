.DEFAULT_GOAL := help

PACKAGE_NAME  := fusilly


help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {sub("\\\\n",sprintf("\n%22c"," "), $$2);printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

cleanmeta:
	-rm -rf ${PACKAGE_NAME}.egg-info

clean: cleanmeta ## removes build-related files
	-rm -f *.deb
	-rm -rf dist
	-rm -rf build
	-find . -type f -name ".*.py" -exec rm -f "{}" \;
	-rm -f *.deb
	-rm -f .coverage
	-find . -type f -name "*.orig" -exec rm -f "{}" \;
	-find . -type f -name "*.rej" -exec rm -f "{}" \;
	-find . -type f -name "*.pyc" -exec rm -f "{}" \;
	-find . -type f -name "*.parse-index" -exec rm -f "{}" \;

sdist: cleanmeta ## Make a source distribution
	python setup.py sdist

bdist: cleanmeta ## Make an egg distribution
	python setup.py bdist_egg

install: ## Install package
	python setup.py install

publish: ## Publish to pypi.i.wish.com
	python setup.py sdist upload -r http://pypi.i.wish.com

test: ## Run unit tests
	py.test

shell: ## Run ipython shell
	@ipython -c 'from ${PACKAGE_NAME} import *' -i


WATCH_FILES=fd -e .py

entr-warn:
	@echo "-------------------------------------------------"
	@echo " ! File watching functionality non-operational ! "
	@echo "                                                 "
	@echo " Install entr(1) to run tasks on file change.    "
	@echo " See http://entrproject.org/                     "
	@echo "-------------------------------------------------"

watch: ## Watch for code changes and run tests as code changes
	if command -v entr > /dev/null; then ${WATCH_FILES} | \
        entr -c $(MAKE) test; else $(MAKE) test entr-warn; fi

coverage: ## Run coverage report
	pytest --cov=./ ${PACKAGE_NAME}/test

.PHONY: help,cleanmeta,clean,sdist,bdist,install,publish,test,entr-warn,watch-test,coverage
