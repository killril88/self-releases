SHELL := /bin/bash
.ONESHELL:
.SILENT:
.SHELLFLAGS := -Eeuo pipefail -c

ROOT := /var/www/zhilibyli/frontend_releases
RELEASES := $(ROOT)/releases
SHARED := $(ROOT)/shared
APP_USER := zhilibyli
APP_GROUP := zhilibyli
TOOL_BIN := $(SHARED)/node-v24.14.0/bin
REPO := git@github.com:ifksco/zhili_byli_frontend_new.git
BRANCH ?= master
SUPERVISOR_HELPER := sudo -n /usr/local/sbin/zb-front-supervisor
TELEGRAM_NOTIFY_ENABLED := 0
BUILD_TELEGRAM_BOT_TOKEN := $(shell grep -m1 '^BUILD_TELEGRAM_BOT_TOKEN=' $(SHARED)/.env.local 2>/dev/null | cut -d= -f2- | tr -d '"')
BUILD_TELEGRAM_CHAT_ID := $(shell grep -m1 '^BUILD_TELEGRAM_CHAT_ID=' $(SHARED)/.env.local 2>/dev/null | cut -d= -f2- | tr -d '"')
COMMITS ?= $(SHORT_COMMIT)
FORCE ?= 0

REMOTE_COMMIT := $(shell git ls-remote $(REPO) refs/heads/$(BRANCH) 2>/dev/null | awk '{print $$1}')
SHORT_COMMIT := $(shell printf '%s' '$(REMOTE_COMMIT)' | cut -c1-8)
CURRENT_COMMIT := $(shell git -C $(ROOT)/current rev-parse HEAD 2>/dev/null)
ifndef RELEASE_ID
RELEASE_ID := $(shell date +%Y%m%d-%H%M%S)-$(SHORT_COMMIT)
endif
RELEASE_PATH := $(RELEASES)/$(RELEASE_ID)

.PHONY: guard-user guard-new-commit notify-start notify-success notify-error status prepare-release build-release set-candidate test-candidate release-steps release promote prod-deploy rollback

guard-user:
	if [[ $$(id -un) != "$(APP_USER)" ]]; then
		echo "Run as $(APP_USER): make <target>"
		exit 1
	fi

guard-new-commit:
	if [[ "$(FORCE)" != "1" && -n "$(CURRENT_COMMIT)" && "$(CURRENT_COMMIT)" == "$(REMOTE_COMMIT)" ]]; then
		echo "No new commit to release"
		exit 1
	fi
	if [[ -z "$(REMOTE_COMMIT)" ]]; then
		echo "Unable to resolve $(BRANCH) from origin"
		exit 1
	fi

# Telegram notifications: same messages as the legacy frontend_v2 Makefile.
notify-start:
	@if [[ "$(TELEGRAM_NOTIFY_ENABLED)" == "1" && -n "$(BUILD_TELEGRAM_BOT_TOKEN)" && -n "$(BUILD_TELEGRAM_CHAT_ID)" ]]; then \
		curl -fsS --max-time 10 -X POST "https://api.telegram.org/bot$(BUILD_TELEGRAM_BOT_TOKEN)/sendMessage" \
			--data-urlencode "chat_id=$(BUILD_TELEGRAM_CHAT_ID)" \
			--data-urlencode "text=⏳ Деплой ZB-FRONT запущен!$$(printf '\n')Изменения:$$(printf '\n')$(COMMITS)" >/dev/null \
		|| echo "Telegram start notification failed" >&2; \
	else echo "Telegram notification skipped: disabled or not configured" >&2; fi

notify-success:
	@if [[ "$(TELEGRAM_NOTIFY_ENABLED)" == "1" && -n "$(BUILD_TELEGRAM_BOT_TOKEN)" && -n "$(BUILD_TELEGRAM_CHAT_ID)" ]]; then \
		curl -fsS --max-time 10 -X POST "https://api.telegram.org/bot$(BUILD_TELEGRAM_BOT_TOKEN)/sendMessage" \
			--data-urlencode "chat_id=$(BUILD_TELEGRAM_CHAT_ID)" \
			--data-urlencode "text=🚀 Деплой ZB-FRONT успешно завершен!$$(printf '\n')Изменения:$$(printf '\n')$(COMMITS)" >/dev/null \
		|| echo "Telegram success notification failed" >&2; \
	else echo "Telegram notification skipped: disabled or not configured" >&2; fi

notify-error:
	@if [[ "$(TELEGRAM_NOTIFY_ENABLED)" == "1" && -n "$(BUILD_TELEGRAM_BOT_TOKEN)" && -n "$(BUILD_TELEGRAM_CHAT_ID)" ]]; then \
		curl -fsS --max-time 10 -X POST "https://api.telegram.org/bot$(BUILD_TELEGRAM_BOT_TOKEN)/sendMessage" \
			--data-urlencode "chat_id=$(BUILD_TELEGRAM_CHAT_ID)" \
			--data-urlencode "text=❌ Ошибка ZB-FRONT при деплое!" >/dev/null \
		|| echo "Telegram error notification failed" >&2; \
	else echo "Telegram notification skipped: disabled or not configured" >&2; fi

status: guard-user
	echo "Branch:    $(BRANCH)"
	echo "Origin:    $(REMOTE_COMMIT)"
	echo "Candidate: $$(readlink $(ROOT)/candidate 2>/dev/null || echo not-set)"
	echo "Current:   $$(readlink $(ROOT)/current 2>/dev/null || echo not-set)"
	echo "Releases:"
	find $(RELEASES) -mindepth 1 -maxdepth 1 -type d -printf '  %f\n' | sort
	echo "Supervisor:"
	$(SUPERVISOR_HELPER) status || true

prepare-release: guard-user
	test ! -e "$(RELEASE_PATH)"
	git clone --branch "$(BRANCH)" --single-branch "$(REPO)" "$(RELEASE_PATH)"
	git -C "$(RELEASE_PATH)" checkout --detach "$(REMOTE_COMMIT)"
	ln -s ../../shared/.env.local "$(RELEASE_PATH)/.env.local"
	echo "Prepared $(RELEASE_ID) at $(REMOTE_COMMIT)"

build-release: guard-user
	test -d "$(RELEASE_PATH)/.git"
	env PATH="$(TOOL_BIN):/usr/local/bin:/usr/bin:/bin" bash -lc '
		set -e
		cd "$(RELEASE_PATH)"
		node bin/sync-vendors.mjs
		pnpm install --frozen-lockfile
		pnpm run --filter search-widget build
		pnpm run --filter main build
	'
	test -s "$(RELEASE_PATH)/apps/zhilibyli/.next/BUILD_ID"
	printf 'BUILD_ID: '
	cat "$(RELEASE_PATH)/apps/zhilibyli/.next/BUILD_ID"

set-candidate: guard-user
	test -s "$(RELEASE_PATH)/apps/zhilibyli/.next/BUILD_ID"
	ln -s "releases/$(RELEASE_ID)" "$(ROOT)/candidate.new"
	mv -Tf "$(ROOT)/candidate.new" "$(ROOT)/candidate"
	echo "Candidate -> releases/$(RELEASE_ID)"

test-candidate: guard-user
	test -s "$(ROOT)/candidate/apps/zhilibyli/.next/BUILD_ID"
	$(SUPERVISOR_HELPER) candidate-stop >/dev/null 2>&1 || true
	trap '$(SUPERVISOR_HELPER) candidate-stop >/dev/null 2>&1 || true' EXIT
	$(SUPERVISOR_HELPER) candidate-start
	sleep 7
	curl -fsS --max-time 10 -H 'Host: zhilibyli.ru' http://127.0.0.1:3010/api/health
	echo
	curl -fsS -o /dev/null --max-time 15 -H 'Host: zhilibyli.ru' http://127.0.0.1:3010/
	printf 'Candidate BUILD_ID: '
	cat "$(ROOT)/candidate/apps/zhilibyli/.next/BUILD_ID"
	echo "Candidate test passed"

release-steps: prepare-release build-release set-candidate test-candidate

release: guard-user guard-new-commit
	@$(MAKE) --no-print-directory notify-start COMMITS="$(COMMITS)"
	@if $(MAKE) --no-print-directory release-steps RELEASE_ID="$(RELEASE_ID)" BRANCH="$(BRANCH)"; then \
		echo "Release $(RELEASE_ID) built and tested as candidate. Production was not switched."; \
	else \
		status=$$?; \
		$(MAKE) --no-print-directory notify-error; \
		exit $$status; \
	fi

promote: guard-user
	test -L "$(ROOT)/candidate"
	test -L "$(ROOT)/current"
	new_target="$$(readlink "$(ROOT)/candidate")"
	old_target="$$(readlink "$(ROOT)/current")"
	test -n "$$new_target"
	test -n "$$old_target"
	test -s "$(ROOT)/$$new_target/apps/zhilibyli/.next/BUILD_ID"
	rollback() {
		set +e
		echo "Promotion failed; restoring $$old_target"
		ln -s "$$old_target" "$(ROOT)/current.rollback"
		mv -Tf "$(ROOT)/current.rollback" "$(ROOT)/current"
		$(SUPERVISOR_HELPER) release-restart
		$(MAKE) --no-print-directory notify-error || true
		exit 1
	}
	trap rollback ERR
	ln -s "$$old_target" "$(ROOT)/previous.new"
	mv -Tf "$(ROOT)/previous.new" "$(ROOT)/previous"
	ln -s "$$new_target" "$(ROOT)/current.new"
	mv -Tf "$(ROOT)/current.new" "$(ROOT)/current"
	$(SUPERVISOR_HELPER) release-restart
	sleep 10
	curl -fsS --max-time 5 -H 'Host: zhilibyli.ru' http://127.0.0.1:3000/api/health >/dev/null
	curl -fsS --max-time 5 -H 'Host: zhilibyli.ru' http://127.0.0.1:3001/api/health >/dev/null
	curl -fsS --max-time 5 -H 'Host: zhilibyli.ru' http://127.0.0.1:3002/api/health >/dev/null
	for attempt in {1..5}; do curl -fsS --max-time 10 https://zhilibyli.ru/api/health >/dev/null; done
	trap - ERR
	echo "Promoted: $$new_target"
	printf 'BUILD_ID: '
	cat "$(ROOT)/current/apps/zhilibyli/.next/BUILD_ID"
	$(MAKE) --no-print-directory notify-success COMMITS="$(COMMITS)"

prod-deploy: release promote
	@echo "Safe production deployment completed: $(RELEASE_ID)"

rollback: guard-user
	test -L "$(ROOT)/previous"
	previous_target="$$(readlink "$(ROOT)/previous")"
	current_target="$$(readlink "$(ROOT)/current")"
	test -s "$(ROOT)/$$previous_target/apps/zhilibyli/.next/BUILD_ID"
	ln -s "$$current_target" "$(ROOT)/previous.new"
	ln -s "$$previous_target" "$(ROOT)/current.new"
	mv -Tf "$(ROOT)/previous.new" "$(ROOT)/previous"
	mv -Tf "$(ROOT)/current.new" "$(ROOT)/current"
	$(SUPERVISOR_HELPER) release-restart
	sleep 10
	curl -fsS --max-time 5 -H 'Host: zhilibyli.ru' http://127.0.0.1:3000/api/health >/dev/null
	curl -fsS --max-time 5 -H 'Host: zhilibyli.ru' http://127.0.0.1:3001/api/health >/dev/null
	curl -fsS --max-time 5 -H 'Host: zhilibyli.ru' http://127.0.0.1:3002/api/health >/dev/null
	echo "Rollback completed: $$previous_target"
