.PHONY: help release clean test lint format

.DEFAULT_GOAL := help

# ============================================
# Colors
# ============================================
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
CYAN := \033[0;36m
NC := \033[0m

# ============================================
# Help
# ============================================
help:  ## Show available commands
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo "$(BLUE)         Xiaomi Speaker - Makefile$(NC)"
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================
# Development
# ============================================
install:  ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv sync --extra dev
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

test:  ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest
	@echo "$(GREEN)✓ Tests completed$(NC)"

lint:  ## Run linters (ruff + mypy)
	@echo "$(BLUE)Running linters...$(NC)"
	uv run ruff check src/ tests/
	uv run mypy src/
	@echo "$(GREEN)✓ Linting completed$(NC)"

format:  ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

clean:  ## Clean cache and temporary files
	@echo "$(BLUE)Cleaning cache files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

# ============================================
# Docker
# ============================================
docker-build:  ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t xiaomi-speaker:local .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-up:  ## Start services with docker-compose
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"

docker-down:  ## Stop services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs:  ## Show service logs
	docker-compose logs -f speaker

# ============================================
# Release
# ============================================
release:  ## Create and push version tag
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "$(RED)Error: Working directory has uncommitted changes$(NC)"; \
		echo "$(YELLOW)Please commit or stash your changes before releasing$(NC)"; \
		exit 1; \
	fi; \
	LATEST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "none"); \
	echo "$(BLUE)════════════════════════════════════════$(NC)"; \
	echo "$(BLUE)         Release New Version$(NC)"; \
	echo "$(BLUE)════════════════════════════════════════$(NC)"; \
	echo "$(CYAN)Current latest tag: $(GREEN)$$LATEST_TAG$(NC)"; \
	echo "$(BLUE)════════════════════════════════════════$(NC)"; \
	printf "$(YELLOW)Enter new version (e.g., v1.0.0): $(NC)"; \
	read -r VERSION; \
	if [ -z "$$VERSION" ]; then \
		echo "$(RED)Error: Version cannot be empty$(NC)"; \
		exit 1; \
	fi; \
	if ! echo "$$VERSION" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "$(RED)Error: Invalid version format '$$VERSION'$(NC)"; \
		echo "$(YELLOW)Expected format: v1.0.0$(NC)"; \
		exit 1; \
	fi; \
	if git tag | grep -q "^$$VERSION$$"; then \
		echo "$(RED)Error: Tag $$VERSION already exists$(NC)"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "$(YELLOW)About to create and push tag: $(GREEN)$$VERSION$(NC)"; \
	printf "$(YELLOW)Continue? [y/N] $(NC)"; \
	read -r CONFIRM; \
	if [ "$$CONFIRM" != "y" ] && [ "$$CONFIRM" != "Y" ]; then \
		echo "$(YELLOW)Aborted$(NC)"; \
		exit 1; \
	fi; \
	if git config user.signingkey >/dev/null 2>&1 && command -v gpg >/dev/null 2>&1; then \
		echo "$(BLUE)Creating GPG signed tag $$VERSION...$(NC)"; \
		if git tag -s $$VERSION -m "Release $$VERSION" 2>/dev/null; then \
			echo "$(GREEN)✓ Signed tag $$VERSION created (Verified ✓)$(NC)"; \
		else \
			echo "$(YELLOW)⚠ GPG signing failed, using regular tag...$(NC)"; \
			git tag -a $$VERSION -m "Release $$VERSION"; \
			echo "$(GREEN)✓ Tag $$VERSION created$(NC)"; \
		fi \
	else \
		echo "$(BLUE)Creating tag $$VERSION...$(NC)"; \
		git tag -a $$VERSION -m "Release $$VERSION"; \
		echo "$(GREEN)✓ Tag $$VERSION created$(NC)"; \
		echo "$(YELLOW)💡 Tip: Configure GPG key to show Verified badge$(NC)"; \
	fi; \
	echo "$(BLUE)Pushing tag to remote...$(NC)"; \
	git push origin $$VERSION; \
	echo "$(GREEN)✓ Release $$VERSION completed$(NC)"
