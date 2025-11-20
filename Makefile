## Top-level Makefile
##
## Each app (backend, user-web, admin-web, etc.) should define its own
## Makefile with app-specific commands. This file can be used to provide
## convenient shortcuts that delegate into those project-level Makefiles.

.PHONY: backend-install backend-dev backend-test backend-lint

backend-install:
	$(MAKE) -C apps/backend install

backend-dev:
	$(MAKE) -C apps/backend dev

backend-test:
	$(MAKE) -C apps/backend test

backend-lint:
	$(MAKE) -C apps/backend lint


