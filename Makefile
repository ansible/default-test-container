.PHONY: build
build:
	podman build -t default-test-container .

.PHONY: update
update:
	./update.py

.PHONY: freeze
freeze:
	./freeze.py default-test-container-freezer
