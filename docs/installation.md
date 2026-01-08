# インストールガイド
## 要件

- Python 3.12以上
- pip（最新推奨版）
- Git（GitHub連携時）
## インストール方法
### PyPIからインストール（推奨版）
```bash
pip install devbuddy-ai
```

### ソースからインストール

```bash
git clone https://github.com/devbuddy/devbuddy-ai.git
cd devbuddy-ai
pip install -e .
```

### 開発用インストール

```bash
pip install -e ".[dev]"
```

## APIキー設定
DevBuddyAIはAI分析にClaude APIまたはOpenAI APIを使用します。
### 環境変数設定
**Linux/macOS:**
```bash
export DEVBUDDY_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:DEVBUDDY_API_KEY = "your_api_key_here"
```

**Windows (cmd):**
```cmd
set DEVBUDDY_API_KEY=your_api_key_here
```

### 永続化

`.bashrc`または`.zshrc`に追加:
```bash
export DEVBUDDY_API_KEY=your_api_key_here
```

## インストール確認
```bash
devbuddy --version
```

正常にインストールされていれば、バージョン情報が表示されます。
## オプション依存関係
### 静的解析ツール

```bash
pip install flake8 mypy pylint
```

### GitHub連携

```bash
pip install PyGithub
export GITHUB_TOKEN=your_github_token
```

## トラブルシューティング

### "command not found"エラー

PATHにPythonのbin/Scriptsディレクトリが含まれているか確認
```bash
python -m devbuddy --version
```

### 依存関係エラー

```bash
pip install --upgrade pip
pip install devbuddy-ai --force-reinstall
```

### APIキーエラー

1. 環境変数が正しく設定されているか確認
2. APIキーが有効か確認
3. 必要な権限があるか確認
