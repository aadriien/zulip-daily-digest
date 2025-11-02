# RC Zulip Daily Digest

POETRY ?= poetry
VENV_DIR = .venv
PYTHON_VERSION = python3

ACTIVATE_VENV = source $(VENV_DIR)/bin/activate &&

.PHONY: setup run-client run-service clean 

all: setup run-client

# Install Poetry dependencies & set up venv
setup:
	@which poetry > /dev/null || (echo "Poetry not found. Installing..."; curl -sSL https://install.python-poetry.org | $(PYTHON_VERSION) -)
	@$(POETRY) config virtualenvs.in-project true  # Ensure virtualenv is inside project folder
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment not found. Creating..."; \
		$(POETRY) env use $(PYTHON_VERSION); \
		$(POETRY) install --no-root --quiet; \
	fi


# Run bot as one-off client instance
run-client: 
	@$(ACTIVATE_VENV) $(POETRY) run python bot.py --client

# Run bot as live service instance
run-service: 
	@$(ACTIVATE_VENV) $(POETRY) run python bot.py --service


clean:
	@echo "Removing virtual environment..."
	@rm -rf .venv

	
