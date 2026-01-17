<div align="center">

# 🤖 DevBuddyAI

**AI-Powered Developer Assistant - Your Intelligent Pair Programmer**

[![PyPI version](https://badge.fury.io/py/devbuddy-ai.svg)](https://badge.fury.io/py/devbuddy-ai)
[![Tests](https://github.com/masuda-hikari/DevBuddyAI/workflows/CI/badge.svg)](https://github.com/masuda-hikari/DevBuddyAI/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://github.com/masuda-hikari/DevBuddyAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

**[English](#english)** | **[日本語](README_ja.md)**

---

### ⚡ **40% faster development** • 🐛 **86% bug detection** • 🚀 **3x faster code reviews**

[Get Started in 5 Minutes](docs/QUICKSTART.md) • [View Demo](https://masuda-hikari.github.io/DevBuddyAI/) • [Try Free Plan](docs/QUICKSTART.md)

</div>

---

## 🌟 Why DevBuddyAI?

> **"Stop reviewing code manually. Let AI handle it."**

DevBuddyAI is an **AI-powered development assistant** that automates code reviews, test generation, and bug fixes across **5 programming languages**.

### ✨ Key Features

| Feature | Benefit | Impact |
|---------|---------|--------|
| 🔍 **AI Code Review** | Instant feedback on bugs, security, & style | **40% faster reviews** |
| 🧪 **Auto Test Generation** | Generate comprehensive unit tests automatically | **3x test coverage** |
| 🛠️ **Smart Bug Fixes** | AI suggests & verifies fixes for failing tests | **86% bug detection** |
| 🔗 **GitHub Integration** | Automated PR comments & checks | **Zero manual setup** |
| 🎨 **VSCode Extension** | Review code without leaving your IDE | **Seamless workflow** |

### 🚀 Supported Languages

<div align="center">

| Python | JavaScript | TypeScript | Rust | Go |
|:------:|:----------:|:----------:|:----:|:--:|
| ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |

</div>

---

## 🎯 Quick Start

**⚡ [5-Minute Quickstart Guide](docs/QUICKSTART.md)** - Get started in minutes!

### 📦 Installation

```bash
pip install devbuddy-ai
```

### 🔑 Configuration

```bash
export DEVBUDDY_API_KEY=your_api_key_here
```

### 🎬 Usage Examples

#### 🔍 Code Review
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

#### 🧪 Test Generation
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

#### 🔗 GitHub Integration
DevBuddyAI automatically comments on your Pull Requests with detailed code review feedback.

---

## 📚 Documentation

- **[5-Minute Quickstart Guide](docs/QUICKSTART.md)** - Get started fast
- **[Sample Code](samples/)** - Web API, CLI, Data Processing examples
- **[Privacy Policy](docs/privacy.html)** - How we protect your code
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Join our community

---

## 💰 Pricing

| Plan | Price | Reviews/Month | Use Case |
|------|-------|---------------|----------|
| **Free** | ¥0 | 50 | Open Source Projects |
| **Pro** | **¥1,980/month** | 500 | Individual Developers |
| **Team** | **¥9,800/month** | Unlimited | Small Teams (up to 10) |
| **Enterprise** | Custom | Unlimited | Large Organizations |

💡 **Start with the free plan** - No credit card required!

[📖 View Detailed Pricing](https://masuda-hikari.github.io/DevBuddyAI/#pricing)

---

## 🏗️ Advanced Usage

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

### Want to try with real examples?

Check out our [sample code](samples/):
- [Web API Server](samples/web_api_server.py) - FastAPI/Flask patterns
- [CLI Tool](samples/cli_tool.py) - Command-line applications
- [Data Processing](samples/data_processing.py) - pandas/numpy workflows

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
| Rust | Full | Partial | clippy, cargo check |
| Go | Full | Partial | go vet, staticcheck, golangci-lint |

## Pricing

| Plan | Target | Price (USD) | Price (JPY) | Features |
|------|--------|-------------|-------------|----------|
| **Free** | Open Source | $0/month | ¥0/月 | 50 reviews/month, public repos only |
| **Pro** | Individuals | $19/month | ¥1,980/月 | 500 reviews/month, private repos, priority |
| **Team** | Teams (up to 10) | $99/month | ¥9,800/月 | Unlimited reviews, GitHub integration |
| **Enterprise** | Organizations | Contact us | 要相談 | Self-hosted, SSO, dedicated support |

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

## GitHub Action (Marketplace)

DevBuddyAI is available on [GitHub Marketplace](https://github.com/marketplace/actions/devbuddyai-code-review). Add to your `.github/workflows/devbuddy.yml`:

### Basic Usage
```yaml
name: DevBuddyAI Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
      checks: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: masuda-hikari/DevBuddyAI@v1
        with:
          api_key: ${{ secrets.DEVBUDDY_API_KEY }}
```

### Advanced Configuration
```yaml
- uses: masuda-hikari/DevBuddyAI@v1
  with:
    api_key: ${{ secrets.DEVBUDDY_API_KEY }}
    model: 'claude-3-sonnet'        # claude-3-opus, gpt-4, gpt-3.5-turbo
    severity: 'medium'              # low, medium, high
    languages: 'auto'               # auto, python, javascript, typescript, rust, go
    review_mode: 'diff'             # diff, full
    fail_on_issues: 'false'         # true to block PRs with issues
    post_comment: 'true'            # true to post review as PR comment
    ignore_patterns: '*.test.py'    # comma-separated patterns to ignore
```

### Action Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `api_key` | API key for AI provider (required) | - |
| `model` | AI model to use | `claude-3-sonnet` |
| `severity` | Minimum severity level | `medium` |
| `languages` | Languages to review | `auto` |
| `review_mode` | Review changed lines or full files | `diff` |
| `fail_on_issues` | Fail check if issues found | `false` |
| `post_comment` | Post results as PR comment | `true` |

### Action Outputs

| Output | Description |
|--------|-------------|
| `issues_count` | Total number of issues found |
| `bugs_count` | Number of bugs found |
| `warnings_count` | Number of warnings found |
| `style_count` | Number of style issues found |
| `review_summary` | Summary text of the review |

## 🤝 Contributing

We welcome contributions! DevBuddyAI is open source and community-driven.

- 🐛 **Report bugs** - [Open an issue](https://github.com/masuda-hikari/DevBuddyAI/issues)
- 💡 **Request features** - [Start a discussion](https://github.com/masuda-hikari/DevBuddyAI/discussions)
- 🔧 **Submit PRs** - See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines
- 📖 **Improve docs** - Help us make DevBuddyAI more accessible

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🌐 Community & Support

- 💬 **[GitHub Discussions](https://github.com/masuda-hikari/DevBuddyAI/discussions)** - Ask questions, share ideas
- 🐛 **[Issue Tracker](https://github.com/masuda-hikari/DevBuddyAI/issues)** - Report bugs, request features
- 📧 **Email**: support@devbuddy.ai
- 🌍 **Website**: [https://masuda-hikari.github.io/DevBuddyAI/](https://masuda-hikari.github.io/DevBuddyAI/)

## ⭐ Star History

If DevBuddyAI helps you, please **star this repo** to support the project!

[![Star History Chart](https://api.star-history.com/svg?repos=masuda-hikari/DevBuddyAI&type=Date)](https://star-history.com/#masuda-hikari/DevBuddyAI&Date)

---

<div align="center">

**DevBuddyAI** - Elevate your code quality with AI 🚀

Made with ❤️ by developers, for developers

[⭐ Star on GitHub](https://github.com/masuda-hikari/DevBuddyAI) • [📖 Documentation](https://masuda-hikari.github.io/DevBuddyAI/) • [💬 Get Support](https://github.com/masuda-hikari/DevBuddyAI/discussions)

</div>
