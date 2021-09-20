.PHONY: build
build:
	docker build -t default-test-container .

.PHONY: update
update:
	./update.py

.PHONY: freeze
freeze:
	./freeze.py default-test-container-freezer
