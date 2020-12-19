.PHONY: test
test:
	poetry run py.test

.PHONY: test-cov
test-cov:
	poetry run py.test --cov=.

.PHONY: test-watch
test-watch:
	poetry run ptw -- --testmon

.PHONY: migrate
migrate:
	poetry run python manage.py migrate

.PHONY: migrations
migrations:
	poetry run python manage.py makemigrations

.PHONY: run
run:
	poetry run python manage.py runserver 0.0.0.0:8014

.PHONY: shell
shell:
	poetry run python manage.py shell

.PHONY: superuser
superuser:
	poetry run python manage.py createsuperuser

.PHONY: cd
cd:
	make build && make push && make deploy

.PHONY: messages
messages:
	poetry run python manage.py makemessages -a 

.PHONY: compile-messages
compile-messages:
	poetry run python manage.py compilemessages

.PHONY: build
build:
	poetry run python setup.py sdist bdist_wheel

.PHONY: release
release:
	twine upload dist/*

