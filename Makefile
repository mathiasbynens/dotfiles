CONTAINERS := $(shell docker ps -aq --filter "label=type=dotfiles")

# Defaults value to master branch
BRANCH ?= master

SHA := $(shell curl -s 'https://api.github.com/repos/dmorand17/dotfiles/git/refs/heads/$(BRANCH)' | jq -r '.object.sha')

build: ## Build dotfiles container. [BRANCH]=branch to build (defaults to 'master')
	@echo "gitsha1 -> $(SHA)"
ifeq ($(SHA),null)
	$(error SHA is not set.  Please ensure that [$(BRANCH)] exists)
endif
	docker build --file docker/Dockerfile --build-arg BRANCH=$(BRANCH) --build-arg SHA=$(SHA) -t dotfiles:latest .

test: ## Test dotfiles using docker
	docker run -e LANG="en_US.UTF-8" -e LANGUAGE="en_US.UTF-8" --label type=dotfiles -it dotfiles /bin/bash

clean: ## Clean dotfiles docker containers/images
ifneq ($(CONTAINERS),)
	@echo "Removing containers: $(CONTAINERS)"
	docker rm $(CONTAINERS)
	docker image prune -f
else
	@echo "Nothing to clean..."
endif

update_submodules: ## Update submodules
	@echo "Updating submodules..."
	git submodule update --remote --rebase

link: ## TODO: Links files for shell
	@echo "Linking dotfiles..."

upgrade: ## Update the local repository, and run any updates
	@echo "Updating..."
	zplug update
	update_submodules

bootstrap: ## Bootstrap system (install/configure apps, link dotfiles)
	@echo "Bootstrapping system..."
	./bootstrap

bootstrap-min: ## Bootstrap minimum necessary (vim, profile, aliases)
	@echo "Bootstrapping minimum configuration..."
	ln -fs shell/.aliases ${HOME}/.aliases
	ln -fs shell/.profile ${HOME}/.profile

function: ## TODO Perform function(s) defined from bootstrap script
	@echo "Performing function(s)..."
ifneq ($(FUNCTION),)
	@for f in $(FUNCTION); do echo " > [$$f]"; done
else
	@echo "Must pass at least 1 FUNCTION value"
endif

.PHONY: build test clean update_submodules link function bootstrap upgrade bootstrap-min

# Automatically build a help menu
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "; printf "\033[31m\nHelp Commands\033[0m\n--------------------------------\n"}; {printf "\033[32m%-22s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
