# GNU Makefile that documents and automates common development operations
#              using the GNU make tool (version >= 3.81)
# Development is typically conducted on Linux or Max OS X (with the Xcode
#              command-line tools installed), so this Makefile is designed
#              to work in that environment (and not on Windows).
# USAGE: Behavioral-Reponses$ make [TARGET]

.PHONY=help
help:
	@echo "USAGE: make [TARGET]"
	@echo "TARGETS:"
	@echo "help       : show help message"
	@echo "clean      : remove .pyc files and local package"
	@echo "package    : build and install local package"
	@echo "pytest-cps : generate report for and cleanup after"
	@echo "             pytest -m 'not requires_pufcsv and not pre_release'"
	@echo "pytest     : generate report for and cleanup after"
	@echo "             pytest -m 'not pre_release'"
	@echo "pytest-all : generate report for and cleanup after"
	@echo "             pytest -m ''"
	@echo "cstest     : generate coding-style errors using the"
	@echo "             pycodestyle (nee pep8) and pylint tools"
	@echo "coverage   : generate test coverage report"
	@echo "git-sync   : synchronize local, origin, and upstream Git repos"
	@echo "git-pr N=n : create local pr-n branch containing upstream PR"

.PHONY=clean
clean:
	@find . -name *pyc -exec rm {} \;
	@find . -name *cache -maxdepth 1 -exec rm -r {} \;
	@conda uninstall behresp --yes --quiet 2>&1 > /dev/null

.PHONY=package
package:
	@pbrelease Behavioral-Responses behresp 0.0.0 --local .

define pytest-cleanup
find . -name *cache -maxdepth 1 -exec rm -r {} \;
rm -f df-??-#-*
rm -f tmp??????-??-#-tmp*
endef

.PHONY=pytest-cps
pytest-cps:
	@cd taxcalc ; pytest -n4 -m "not requires_pufcsv and not pre_release"
	@$(pytest-cleanup)

.PHONY=pytest
pytest:
	@cd behresp ; pytest -n4 -m "not pre_release"
	@$(pytest-cleanup)

.PHONY=pytest-all
pytest-all:
	@cd behresp ; pytest -n4 -m ""
	@$(pytest-cleanup)

JSON_FILES := $(shell find . -name "*json" | grep -v htmlcov)
PYLINT_FILES := $(shell grep -rl --include="*py" disable=locally-disabled .)
PYLINT_OPTIONS = --disable=locally-disabled --score=no --jobs=4

.PHONY=cstest
cstest:
	-pycodestyle behresp
	@-pycodestyle --ignore=E501,E121 $(JSON_FILES)
	@-pylint $(PYLINT_OPTIONS) $(PYLINT_FILES)

define coverage-cleanup
rm -f .coverage htmlcov/*
endef

COVMARK = "not pre_release"

OS := $(shell uname -s)

.PHONY=coverage
coverage:
	@$(coverage-cleanup)
	@coverage run -m pytest -v -m $(COVMARK) > /dev/null
	@coverage html --ignore-errors
ifeq ($(OS), Darwin) # on Mac OS X
	@open htmlcov/index.html
else
	@echo "Open htmlcov/index.html in browser to view report"
endif
	@$(pytest-cleanup)

.PHONY=git-sync
git-sync:
	@./gitsync

.PHONY=git-pr
git-pr:
	@./gitpr $(N)
