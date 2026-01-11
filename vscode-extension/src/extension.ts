/**
 * DevBuddyAI VSCode拡張
 * AI開発者支援ツール - コードレビュー、テスト生成、バグ修正提案
 */

import * as vscode from 'vscode';
import { DevBuddyClient } from './client';
import { IssueTreeProvider } from './providers/issueTreeProvider';
import { TestTreeProvider } from './providers/testTreeProvider';
import { UsageTreeProvider } from './providers/usageTreeProvider';
import { DiagnosticManager } from './diagnostics';

let client: DevBuddyClient;
let diagnosticManager: DiagnosticManager;
let issueTreeProvider: IssueTreeProvider;
let testTreeProvider: TestTreeProvider;
let usageTreeProvider: UsageTreeProvider;
let statusBarItem: vscode.StatusBarItem;

/**
 * 拡張機能アクティベート時の処理
 */
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    console.log('DevBuddyAI: 拡張機能をアクティベート中...');

    // クライアント初期化
    client = new DevBuddyClient();
    diagnosticManager = new DiagnosticManager();

    // ツリービュープロバイダー初期化
    issueTreeProvider = new IssueTreeProvider();
    testTreeProvider = new TestTreeProvider();
    usageTreeProvider = new UsageTreeProvider(client);

    // ツリービュー登録
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('devbuddy.issues', issueTreeProvider),
        vscode.window.registerTreeDataProvider('devbuddy.tests', testTreeProvider),
        vscode.window.registerTreeDataProvider('devbuddy.usage', usageTreeProvider)
    );

    // ステータスバーアイテム作成
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '$(search) DevBuddyAI';
    statusBarItem.tooltip = 'DevBuddyAI: クリックでレビュー実行';
    statusBarItem.command = 'devbuddy.reviewFile';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // コマンド登録
    context.subscriptions.push(
        vscode.commands.registerCommand('devbuddy.reviewFile', reviewCurrentFile),
        vscode.commands.registerCommand('devbuddy.reviewSelection', reviewSelection),
        vscode.commands.registerCommand('devbuddy.generateTests', generateTests),
        vscode.commands.registerCommand('devbuddy.suggestFix', suggestFix),
        vscode.commands.registerCommand('devbuddy.setApiKey', setApiKey),
        vscode.commands.registerCommand('devbuddy.showUsage', showUsage)
    );

    // ファイル保存時の自動レビュー（設定が有効な場合）
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(async (document) => {
            const config = vscode.workspace.getConfiguration('devbuddy');
            if (config.get<boolean>('autoReviewOnSave')) {
                await reviewDocument(document);
            }
        })
    );

    // 診断コレクション登録
    context.subscriptions.push(diagnosticManager.getDiagnosticCollection());

    console.log('DevBuddyAI: アクティベート完了');
}

/**
 * 拡張機能ディアクティベート時の処理
 */
export function deactivate(): void {
    console.log('DevBuddyAI: 拡張機能をディアクティベート');
}

/**
 * 現在のファイルをレビュー
 */
async function reviewCurrentFile(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('DevBuddyAI: ファイルが開かれていません');
        return;
    }

    await reviewDocument(editor.document);
}

/**
 * ドキュメントをレビュー
 */
async function reviewDocument(document: vscode.TextDocument): Promise<void> {
    const supportedLanguages = ['python', 'javascript', 'typescript', 'rust', 'go'];
    if (!supportedLanguages.includes(document.languageId)) {
        vscode.window.showWarningMessage(
            `DevBuddyAI: ${document.languageId}は現在サポートされていません`
        );
        return;
    }

    // ステータスバー更新
    statusBarItem.text = '$(sync~spin) DevBuddyAI: レビュー中...';

    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'DevBuddyAI: コードレビュー中...',
                cancellable: true
            },
            async (progress, token) => {
                progress.report({ increment: 0 });

                const code = document.getText();
                const config = vscode.workspace.getConfiguration('devbuddy');

                const result = await client.review(code, {
                    language: document.languageId,
                    severity: config.get<string>('severity') || 'medium',
                    filePath: document.fileName
                });

                if (token.isCancellationRequested) {
                    return;
                }

                progress.report({ increment: 100 });

                // 診断情報更新
                diagnosticManager.updateDiagnostics(document.uri, result.issues);

                // ツリービュー更新
                issueTreeProvider.updateIssues(result.issues);

                // 結果表示
                const issueCount = result.issues.length;
                if (issueCount === 0) {
                    vscode.window.showInformationMessage(
                        'DevBuddyAI: 問題は検出されませんでした'
                    );
                } else {
                    vscode.window.showInformationMessage(
                        `DevBuddyAI: ${issueCount}件の問題を検出しました`
                    );
                }
            }
        );
    } catch (error) {
        handleError('レビュー', error);
    } finally {
        statusBarItem.text = '$(search) DevBuddyAI';
    }
}

/**
 * 選択範囲をレビュー
 */
async function reviewSelection(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('DevBuddyAI: ファイルが開かれていません');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('DevBuddyAI: コードが選択されていません');
        return;
    }

    const selectedCode = editor.document.getText(selection);
    statusBarItem.text = '$(sync~spin) DevBuddyAI: レビュー中...';

    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'DevBuddyAI: 選択範囲をレビュー中...',
                cancellable: true
            },
            async (progress, token) => {
                progress.report({ increment: 0 });

                const config = vscode.workspace.getConfiguration('devbuddy');

                const result = await client.review(selectedCode, {
                    language: editor.document.languageId,
                    severity: config.get<string>('severity') || 'medium',
                    startLine: selection.start.line + 1
                });

                if (token.isCancellationRequested) {
                    return;
                }

                progress.report({ increment: 100 });

                // 結果をパネルに表示
                showResultPanel('コードレビュー結果', formatReviewResult(result));
            }
        );
    } catch (error) {
        handleError('レビュー', error);
    } finally {
        statusBarItem.text = '$(search) DevBuddyAI';
    }
}

/**
 * テスト生成
 */
async function generateTests(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('DevBuddyAI: ファイルが開かれていません');
        return;
    }

    // 選択範囲があればそれを使用、なければ全体
    const selection = editor.selection;
    const code = selection.isEmpty
        ? editor.document.getText()
        : editor.document.getText(selection);

    statusBarItem.text = '$(sync~spin) DevBuddyAI: テスト生成中...';

    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'DevBuddyAI: テスト生成中...',
                cancellable: true
            },
            async (progress, token) => {
                progress.report({ increment: 0, message: 'AIが分析中...' });

                const config = vscode.workspace.getConfiguration('devbuddy');

                const result = await client.generateTests(code, {
                    language: editor.document.languageId,
                    framework: config.get<string>('testFramework') || 'pytest',
                    filePath: editor.document.fileName
                });

                if (token.isCancellationRequested) {
                    return;
                }

                progress.report({ increment: 100 });

                // ツリービュー更新
                testTreeProvider.updateTests(result.tests);

                // 新規ファイルとして開く
                const newDocument = await vscode.workspace.openTextDocument({
                    content: result.testCode,
                    language: editor.document.languageId
                });
                await vscode.window.showTextDocument(newDocument, vscode.ViewColumn.Beside);

                vscode.window.showInformationMessage(
                    `DevBuddyAI: ${result.tests.length}件のテストを生成しました`
                );
            }
        );
    } catch (error) {
        handleError('テスト生成', error);
    } finally {
        statusBarItem.text = '$(search) DevBuddyAI';
    }
}

/**
 * バグ修正提案
 */
async function suggestFix(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('DevBuddyAI: ファイルが開かれていません');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('DevBuddyAI: 修正対象のコードを選択してください');
        return;
    }

    const selectedCode = editor.document.getText(selection);
    statusBarItem.text = '$(sync~spin) DevBuddyAI: 修正提案生成中...';

    try {
        // エラー説明を入力（オプション）
        const errorDescription = await vscode.window.showInputBox({
            prompt: 'エラーや問題の説明（オプション）',
            placeHolder: '例: TypeError: undefined is not a function'
        });

        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'DevBuddyAI: 修正提案生成中...',
                cancellable: true
            },
            async (progress, token) => {
                progress.report({ increment: 0 });

                const result = await client.suggestFix(selectedCode, {
                    language: editor.document.languageId,
                    errorDescription: errorDescription || undefined,
                    filePath: editor.document.fileName
                });

                if (token.isCancellationRequested) {
                    return;
                }

                progress.report({ increment: 100 });

                // 修正提案を表示
                const action = await vscode.window.showInformationMessage(
                    `DevBuddyAI: 修正提案（信頼度: ${Math.round(result.confidence * 100)}%）`,
                    '適用',
                    '詳細表示',
                    'キャンセル'
                );

                if (action === '適用') {
                    // 修正を適用
                    await editor.edit((editBuilder) => {
                        editBuilder.replace(selection, result.fixedCode);
                    });
                    vscode.window.showInformationMessage('DevBuddyAI: 修正を適用しました');
                } else if (action === '詳細表示') {
                    showResultPanel('修正提案', formatFixResult(result));
                }
            }
        );
    } catch (error) {
        handleError('修正提案', error);
    } finally {
        statusBarItem.text = '$(search) DevBuddyAI';
    }
}

/**
 * APIキー設定
 */
async function setApiKey(): Promise<void> {
    const apiKey = await vscode.window.showInputBox({
        prompt: 'DevBuddyAI APIキーを入力',
        password: true,
        placeHolder: 'db_xxxxxxxxxxxxxxxxxxxx'
    });

    if (apiKey) {
        const config = vscode.workspace.getConfiguration('devbuddy');
        await config.update('apiKey', apiKey, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage('DevBuddyAI: APIキーを設定しました');
    }
}

/**
 * 利用状況表示
 */
async function showUsage(): Promise<void> {
    try {
        const usage = await client.getUsage();
        showResultPanel('利用状況', formatUsage(usage));
    } catch (error) {
        handleError('利用状況取得', error);
    }
}

/**
 * 結果パネル表示
 */
function showResultPanel(title: string, content: string): void {
    const panel = vscode.window.createWebviewPanel(
        'devbuddyResult',
        title,
        vscode.ViewColumn.Beside,
        { enableScripts: true }
    );

    panel.webview.html = getWebviewContent(title, content);
}

/**
 * Webviewコンテンツ生成
 */
function getWebviewContent(title: string, content: string): string {
    return `
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>${title}</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    font-size: var(--vscode-font-size);
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                    padding: 20px;
                    line-height: 1.6;
                }
                h1, h2, h3 {
                    color: var(--vscode-editor-foreground);
                    border-bottom: 1px solid var(--vscode-panel-border);
                    padding-bottom: 8px;
                }
                pre {
                    background: var(--vscode-textCodeBlock-background);
                    padding: 12px;
                    border-radius: 4px;
                    overflow-x: auto;
                }
                code {
                    font-family: var(--vscode-editor-font-family);
                }
                .issue {
                    border-left: 3px solid var(--vscode-editorWarning-foreground);
                    padding-left: 12px;
                    margin: 12px 0;
                }
                .issue.error {
                    border-left-color: var(--vscode-editorError-foreground);
                }
                .suggestion {
                    background: var(--vscode-diffEditor-insertedTextBackground);
                    padding: 8px;
                    border-radius: 4px;
                    margin: 8px 0;
                }
            </style>
        </head>
        <body>
            <h1>${title}</h1>
            ${content}
        </body>
        </html>
    `;
}

/**
 * レビュー結果をフォーマット
 */
function formatReviewResult(result: any): string {
    let html = '<h2>検出された問題</h2>';

    if (result.issues.length === 0) {
        html += '<p>問題は検出されませんでした。</p>';
        return html;
    }

    for (const issue of result.issues) {
        const severityClass = issue.severity === 'error' ? 'error' : '';
        html += `
            <div class="issue ${severityClass}">
                <strong>${issue.type}</strong> (行 ${issue.line})
                <p>${issue.message}</p>
                ${issue.suggestion ? `<div class="suggestion"><strong>提案:</strong> ${issue.suggestion}</div>` : ''}
            </div>
        `;
    }

    return html;
}

/**
 * 修正結果をフォーマット
 */
function formatFixResult(result: any): string {
    return `
        <h2>修正提案</h2>
        <p><strong>カテゴリ:</strong> ${result.category}</p>
        <p><strong>信頼度:</strong> ${Math.round(result.confidence * 100)}%</p>
        <h3>説明</h3>
        <p>${result.explanation}</p>
        <h3>修正コード</h3>
        <pre><code>${escapeHtml(result.fixedCode)}</code></pre>
    `;
}

/**
 * 利用状況をフォーマット
 */
function formatUsage(usage: any): string {
    return `
        <h2>プラン: ${usage.plan}</h2>
        <h3>今月の利用状況</h3>
        <ul>
            <li>レビュー: ${usage.reviews.used} / ${usage.reviews.limit}</li>
            <li>テスト生成: ${usage.testgen.used} / ${usage.testgen.limit}</li>
            <li>修正提案: ${usage.fixes.used} / ${usage.fixes.limit}</li>
        </ul>
        <p>リセット日: ${usage.resetDate}</p>
    `;
}

/**
 * HTMLエスケープ
 */
function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * エラーハンドリング
 */
function handleError(operation: string, error: unknown): void {
    console.error(`DevBuddyAI: ${operation}エラー:`, error);

    let message = '不明なエラーが発生しました';
    if (error instanceof Error) {
        if (error.message.includes('API key')) {
            message = 'APIキーが設定されていません。devbuddy.setApiKeyを実行してください';
        } else if (error.message.includes('rate limit')) {
            message = 'API利用制限に達しました。しばらく待ってから再試行してください';
        } else if (error.message.includes('network')) {
            message = 'ネットワークエラーです。接続を確認してください';
        } else {
            message = error.message;
        }
    }

    vscode.window.showErrorMessage(`DevBuddyAI: ${operation}エラー - ${message}`);
}
