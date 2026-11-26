.PHONY: check test package

check:
	python3 scripts/check_repository.py

test:
	python3 -m unittest discover -s tests -v

package: check test
	python3 scripts/package_repository.py
