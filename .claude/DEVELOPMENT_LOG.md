# DevBuddyAI 髢狗匱繝ｭ繧ｰ

## 2026-01-06 繧ｻ繝・す繝ｧ繝ｳ1

### 螳御ｺ・ち繧ｹ繧ｯ
1. **繝励Ο繧ｸ繧ｧ繧ｯ繝亥・譛滓ｧ矩菴懈・**
   - 繝・ぅ繝ｬ繧ｯ繝医Μ讒矩: src/devbuddy/, samples/, tests/, docs/
   - CLAUDE.md: 繝励Ο繧ｸ繧ｧ繧ｯ繝医ぎ繝舌リ繝ｳ繧ｹ繝ｻ謚陦楢ｨｭ險医・繝槭ロ繧ｿ繧､繧ｺ謌ｦ逡･
   - README.md: 陬ｽ蜩∬ｪｬ譏弱・菴ｿ逕ｨ萓九・萓｡譬ｼ諠・ｱ
   - .claude/settings.json: Claude Code讓ｩ髯占ｨｭ螳・
2. **繧ｳ繧｢繧ｨ繝ｳ繧ｸ繝ｳ螳溯｣・*
   - `core/reviewer.py`: AI繧ｳ繝ｼ繝峨Ξ繝薙Η繝ｼ繧ｨ繝ｳ繧ｸ繝ｳ
   - `core/generator.py`: 繝・せ繝育函謌舌お繝ｳ繧ｸ繝ｳ・郁・蟾ｱ讀懆ｨｼ繝ｫ繝ｼ繝嶺ｻ倥″・・   - `core/fixer.py`: 繝舌げ菫ｮ豁｣謠先｡医お繝ｳ繧ｸ繝ｳ
   - `core/models.py`: 蜈ｱ騾壹ョ繝ｼ繧ｿ繝｢繝・Ν・亥ｾｪ迺ｰ繧､繝ｳ繝昴・繝亥屓驕ｿ逕ｨ・・
3. **LLM繧ｯ繝ｩ繧､繧｢繝ｳ繝亥ｮ溯｣・*
   - `llm/client.py`: Claude/OpenAI荳｡蟇ｾ蠢懊け繝ｩ繧､繧｢繝ｳ繝・   - `llm/prompts.py`: 繝励Ο繝ｳ繝励ヨ繝・Φ繝励Ξ繝ｼ繝磯寔

4. **髱咏噪隗｣譫仙ｮ溯｣・*
   - `analyzers/python_analyzer.py`: AST隗｣譫・+ flake8/mypy騾｣謳ｺ

5. **螟夜Κ騾｣謳ｺ螳溯｣・*
   - `integrations/github.py`: GitHub PR騾｣謳ｺ
   - `integrations/git.py`: 繝ｭ繝ｼ繧ｫ繝ｫGit謫堺ｽ・
6. **CLI螳溯｣・*
   - `cli.py`: Click 繝吶・繧ｹ縺ｮCLI・・eview/testgen/fix/config/auth・・
7. **繝・せ繝医せ繧､繝ｼ繝井ｽ懈・**
   - tests/conftest.py, test_reviewer.py, test_generator.py, test_analyzer.py, test_cli.py

8. **CI/CD險ｭ螳・*
   - .github/workflows/ci.yml: lint/test/build繝代う繝励Λ繧､繝ｳ
   - .github/workflows/devbuddy-action.yml: PR閾ｪ蜍輔Ξ繝薙Η繝ｼ

### 讀懷・縺励◆隱ｲ鬘・1. **蠕ｪ迺ｰ繧､繝ｳ繝昴・繝・*: `reviewer.py` 竊・`python_analyzer.py`
   - **蟇ｾ遲・*: `core/models.py`縺ｫIssue/ReviewResult繧貞・髮｢
   - **迥ｶ諷・*: 菫ｮ豁｣荳ｭ・医ヵ繧｡繧､繝ｫ邱ｨ髮・酔譛溷撫鬘後≠繧奇ｼ・
### 谺｡蝗槭ち繧ｹ繧ｯ
1. 蠕ｪ迺ｰ繧､繝ｳ繝昴・繝亥撫鬘後・螳悟・隗｣豎ｺ
2. 繝・せ繝亥ｮ溯｡後・蜈ｨ繝・せ繝亥粋譬ｼ遒ｺ隱・3. flake8/mypy髱咏噪隗｣譫宣夐℃
4. GitHub縺ｸ縺ｮ繝励ャ繧ｷ繝･

### 謚陦薙Γ繝｢
- Python 3.12+ 菴ｿ逕ｨ
- 萓晏ｭ・ click, anthropic, openai, PyGithub, pytest
- 閾ｪ蟾ｱ讀懆ｨｼ繝ｫ繝ｼ繝・ 繝・せ繝育函謌絶・螳溯｡娯・螟ｱ謨玲凾AI縺ｧ菫ｮ豁｣・・ax 3蝗橸ｼ・