# RC Zulip Daily Digest

# Add Poetry's install location to PATH so Make can find it
export PATH := $(HOME)/.local/bin:$(PATH)

POETRY ?= poetry
VENV_DIR = .venv
PYTHON_VERSION = python3

.PHONY: setup run-client run-service wget-model clean

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
	@$(POETRY) run python bot.py --client

# Run bot as live service instance
run-service: 
	@$(POETRY) run python bot.py --service


# Download Qwen model directly on Heap Cluster using wget
wget-model:
	@echo "Downloading Qwen2.5-1.5B-Instruct model..."
	@mkdir -p models
	@cd models && \
		if [ -d "Qwen2.5-1.5B-Instruct" ]; then \
			echo "Model already exists. Skipping download."; \
		else \
			wget -r -np -nH --cut-dirs=1 --reject="index.html*" \
				https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/resolve/main/ && \
			echo "Model download complete!"; \
		fi


clean:
	@echo "Removing virtual environment..."
	@rm -rf .venv

	
