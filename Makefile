.PHONY: build update freeze

build:
	docker build -t default-test-container .

update:
	./update.py

freeze:
	./freeze.sh
