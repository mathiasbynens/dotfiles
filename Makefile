CONTAINERS := $(shell docker ps -aq --filter "label=type=dotfiles")

# Default to master
BRANCH ?= master

SHA := $(shell curl -s 'https://api.github.com/repos/dmorand17/dotfiles/git/refs/heads/$(BRANCH)' | jq -r '.object.sha')

build:
	@echo "gitsha1 -> $(SHA)"
ifeq ($(SHA),null)
	$(error SHA is not set.  Please ensure that [$(BRANCH)] exists)
endif
	docker build --file docker/Dockerfile --build-arg BRANCH=$(BRANCH) --build-arg SHA=$(SHA) -t dotfiles:latest .

test:
	docker run --label type=dotfiles -it dotfiles /bin/bash

clean:
ifneq ($(CONTAINERS),)
	@echo "Removing containers: $(CONTAINERS)"
	docker rm $(CONTAINERS)
	docker image prune -f
else
	@echo "Nothing to clean..."
endif

update_submodules:
	@echo "Updating submodules..."
	git submodule update --remote --rebase

link:
	@echo "linking dotfiles"

.PHONY: build test clean update_submodules