# Developing Axon OS

## Setup

### Prerequisites
- Python 3.10+
- Git

### Install Dependencies

1. **Runtime dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Note: On Ubuntu, some dependencies require system packages:
   ```bash
   sudo apt-get install python3-dbus python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 python3-vte-2.91
   ```

2. **Development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

### Pre-commit Hooks (Optional but Recommended)

Set up automatic code quality checks before each commit:

```bash
pre-commit install
pre-commit run --all-files
```

## Running Tests

Run the test suite:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ --cov=apps --cov=services --cov-report=term-missing
```

## Code Quality

### Linting with Ruff

Check for style and correctness issues:

```bash
ruff check apps/ services/ tests/ installer/
```

Auto-fix issues:

```bash
ruff check --fix apps/ services/ tests/ installer/
```

### Type Checking with mypy

Run type checks:

```bash
mypy apps/ services/ --ignore-missing-imports
```

### Format Code with Black

Format Python code:

```bash
black apps/ services/ tests/ installer/
```

## Project Structure

- **`apps/`** - Desktop applications (UI panels, terminal, file browser, etc.)
- **`services/`** - System services (brain, context engine)
- **`installer/`** - Installation and partitioning tools
- **`shell/`** - GNOME Shell extension
- **`theme/`** - GTK theme, icon theme, wallpapers
- **`tests/`** - Test suite
- **`.github/workflows/`** - CI/CD pipelines

## Logging

Use the centralized logging utility for consistent log output:

```python
from apps.axon_logger import configure_app_logger

logger = configure_app_logger(__name__)
logger.info("App started")
logger.error("Something went wrong: %s", error_msg)
```

## Troubleshooting

### Tests fail on Windows
Many tests require Linux system bindings (dbus, GTK). Run tests on Ubuntu or in WSL2.

### Import errors with gi (PyGObject)
Ensure you've installed the system GTK bindings:
```bash
sudo apt-get install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

### mypy reports unresolved imports
Some D-Bus and GTK types may not have stubs. Use `--ignore-missing-imports` flag.

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and run tests: `pytest tests/`
3. Lint and format: `ruff check --fix` and `black .`
4. Commit with clear message: `git commit -m "feat: description"`
5. Push and open a pull request

## CI Pipeline

The project uses GitHub Actions (`.github/workflows/ci.yml`) to automatically:
- Run tests on Python 3.10, 3.11, 3.12
- Check code with ruff
- Perform type checks with mypy
- Generate coverage reports

See the CI configuration in `.github/workflows/` for details.
