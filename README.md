# DevBuddyAI

**AI-Powered Developer Assistant** - Your intelligent pair programmer that reviews code, generates tests, and suggests fixes.

## Overview

DevBuddyAI leverages advanced AI to assist developers throughout the development lifecycle:

- **Automated Code Reviews**: Get instant feedback on code quality, potential bugs, and style issues
- **Test Generation**: Automatically generate comprehensive unit tests for your functions
- **Bug Fix Suggestions**: Receive AI-powered suggestions to fix failing tests or known issues
- **Multi-Platform Integration**: Use via CLI, GitHub Actions, or IDE plugins

## Features

### Code Review
```bash
$ devbuddy review src/mycode.py

DevBuddyAI Code Review Results:
================================

[WARNING] Line 23: Potential null reference - 'data' may be None
  Suggestion: Add null check before accessing data.items()

[STYLE] Line 45: Function 'processData' should use snake_case
  Suggestion: Rename to 'process_data'

[BUG] Line 67: Division by zero possible when count == 0
  Suggestion: Add guard clause: if count == 0: return 0

Summary: 1 bug, 1 warning, 1 style issue found
```

### Test Generation
```bash
$ devbuddy testgen src/calculator.py --function add

Generated test file: tests/test_calculator.py

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 5) == 5

def test_add_floats():
    assert add(1.5, 2.5) == 4.0

Running generated tests... All 4 tests passed!
```

### GitHub Integration
DevBuddyAI automatically comments on your Pull Requests with detailed code review feedback.

## Installation

```bash
pip install devbuddy-ai
```

Or install from source:
```bash
git clone https://github.com/yourorg/devbuddy-ai.git
cd devbuddy-ai
pip install -e .
```

## Quick Start

### 1. Set up API Key
```bash
export DEVBUDDY_API_KEY=your_api_key_here
```

### 2. Review a File
```bash
devbuddy review path/to/your/code.py
```

### 3. Generate Tests
```bash
devbuddy testgen path/to/your/code.py
```

## Configuration

Create a `.devbuddy.yaml` in your project root:

```yaml
language: python
style_guide: pep8
review:
  severity: medium
  include_suggestions: true
testgen:
  framework: pytest
  coverage_target: 80
ignore_patterns:
  - "*.generated.py"
  - "migrations/*"
```

## Supported Languages

| Language | Review | Test Gen | Static Analysis |
|----------|--------|----------|-----------------|
| Python | Full | Full | flake8, mypy, pylint |
| JavaScript | Full | Partial | ESLint |
| TypeScript | Full | Partial | ESLint, tsc |
| Rust | Coming Soon | Coming Soon | clippy |
| Go | Coming Soon | Coming Soon | go vet |

## Pricing

| Plan | Target | Price | Features |
|------|--------|-------|----------|
| **Free** | Open Source | $0/month | 50 reviews/month, public repos only |
| **Pro** | Individuals | $19/month | 500 reviews/month, private repos, priority |
| **Team** | Teams (up to 10) | $99/month | Unlimited reviews, GitHub integration |
| **Enterprise** | Organizations | Contact us | Self-hosted, SSO, dedicated support |

### Why Pay for DevBuddyAI?

- **Save Time**: Reduce code review time by 40%
- **Catch Bugs Early**: AI catches issues humans miss
- **Consistent Quality**: Enforce coding standards automatically
- **ROI**: One prevented production bug pays for a year of service

## Security & Privacy

**Your code stays secure.**

- Code is processed in memory only - never stored
- API calls use TLS 1.3 encryption
- Enterprise plan offers self-hosted deployment - **no code ever leaves your network**
- SOC 2 Type II compliance (Enterprise)

## CLI Reference

```
Usage: devbuddy [OPTIONS] COMMAND [ARGS]...

Commands:
  review    Review code for bugs, style issues, and improvements
  testgen   Generate unit tests for specified functions
  fix       Suggest fixes for failing tests or known bugs
  config    Manage DevBuddyAI configuration
  auth      Authenticate with DevBuddyAI service

Options:
  --version  Show version and exit
  --help     Show this message and exit

Examples:
  devbuddy review src/              # Review all files in directory
  devbuddy review --diff HEAD~1     # Review only changed files
  devbuddy testgen src/utils.py     # Generate tests for entire file
  devbuddy testgen -f calculate     # Generate tests for specific function
  devbuddy fix tests/test_api.py    # Suggest fixes for failing tests
```

## GitHub Action

Add to your `.github/workflows/devbuddy.yml`:

```yaml
name: DevBuddyAI Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: devbuddy/action@v1
        with:
          api_key: ${{ secrets.DEVBUDDY_API_KEY }}
          review_mode: "diff"
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**DevBuddyAI** - Elevate your code quality with AI.

[Website](https://devbuddy.ai) | [Documentation](https://docs.devbuddy.ai) | [Support](mailto:support@devbuddy.ai)
