.PHONY: build update

build:
	docker build -t default-test-container .

update:
	./update.py
