/**
 * DevBuddyAI APIクライアント
 * CLI/サーバーとの通信を担当
 */

import * as vscode from 'vscode';
import axios, { AxiosInstance, AxiosError } from 'axios';
import { spawn } from 'child_process';
import * as path from 'path';

/** レビューオプション */
export interface ReviewOptions {
    language: string;
    severity?: string;
    filePath?: string;
    startLine?: number;
}

/** テスト生成オプション */
export interface TestGenOptions {
    language: string;
    framework?: string;
    filePath?: string;
}

/** 修正提案オプション */
export interface FixOptions {
    language: string;
    errorDescription?: string;
    filePath?: string;
}

/** 問題 */
export interface Issue {
    type: string;
    severity: string;
    message: string;
    line: number;
    column?: number;
    suggestion?: string;
}

/** レビュー結果 */
export interface ReviewResult {
    issues: Issue[];
    summary?: string;
}

/** テスト情報 */
export interface TestInfo {
    name: string;
    description: string;
}

/** テスト生成結果 */
export interface TestGenResult {
    testCode: string;
    tests: TestInfo[];
}

/** 修正結果 */
export interface FixResult {
    fixedCode: string;
    explanation: string;
    confidence: number;
    category: string;
}

/** 利用状況 */
export interface UsageInfo {
    plan: string;
    reviews: { used: number; limit: number };
    testgen: { used: number; limit: number };
    fixes: { used: number; limit: number };
    resetDate: string;
}

/**
 * DevBuddyAIクライアント
 * CLIまたはHTTP APIを使用してDevBuddyAIサービスと通信
 */
export class DevBuddyClient {
    private httpClient: AxiosInstance | null = null;
    private useHttp: boolean = false;

    constructor() {
        this.initializeClient();
    }

    /**
     * クライアント初期化
     */
    private initializeClient(): void {
        const config = vscode.workspace.getConfiguration('devbuddy');
        const serverUrl = config.get<string>('serverUrl');

        if (serverUrl) {
            this.useHttp = true;
            this.httpClient = axios.create({
                baseURL: serverUrl,
                timeout: 120000, // 2分（AIレスポンス待ち）
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        }
    }

    /**
     * APIキー取得
     */
    private getApiKey(): string {
        const config = vscode.workspace.getConfiguration('devbuddy');
        const apiKey = config.get<string>('apiKey') || process.env.DEVBUDDY_API_KEY;

        if (!apiKey) {
            throw new Error('API key not configured');
        }

        return apiKey;
    }

    /**
     * CLI実行
     */
    private async executeCli(
        command: string,
        args: string[],
        input?: string
    ): Promise<string> {
        return new Promise((resolve, reject) => {
            const config = vscode.workspace.getConfiguration('devbuddy');
            const cliPath = config.get<string>('cliPath') || 'devbuddy';

            const fullArgs = [command, ...args, '--format', 'json'];
            const proc = spawn(cliPath, fullArgs, {
                env: {
                    ...process.env,
                    DEVBUDDY_API_KEY: this.getApiKey()
                }
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            if (input) {
                proc.stdin.write(input);
                proc.stdin.end();
            }

            proc.on('close', (code) => {
                if (code === 0) {
                    resolve(stdout);
                } else {
                    reject(new Error(stderr || `CLI exited with code ${code}`));
                }
            });

            proc.on('error', (error) => {
                reject(new Error(`CLI execution failed: ${error.message}`));
            });
        });
    }

    /**
     * HTTP API呼び出し
     */
    private async callApi<T>(
        endpoint: string,
        data: Record<string, unknown>
    ): Promise<T> {
        if (!this.httpClient) {
            throw new Error('HTTP client not initialized');
        }

        try {
            const response = await this.httpClient.post<T>(endpoint, data, {
                headers: {
                    'Authorization': `Bearer ${this.getApiKey()}`
                }
            });
            return response.data;
        } catch (error) {
            if (error instanceof AxiosError) {
                if (error.response?.status === 401) {
                    throw new Error('API key invalid');
                } else if (error.response?.status === 429) {
                    throw new Error('rate limit exceeded');
                } else if (error.code === 'ECONNREFUSED') {
                    throw new Error('network error: server not reachable');
                }
                throw new Error(
                    error.response?.data?.detail || error.message
                );
            }
            throw error;
        }
    }

    /**
     * コードレビュー
     */
    async review(code: string, options: ReviewOptions): Promise<ReviewResult> {
        if (this.useHttp) {
            return this.callApi<ReviewResult>('/api/v1/review', {
                code,
                language: options.language,
                severity: options.severity || 'medium',
                file_path: options.filePath
            });
        }

        // CLI使用
        const args: string[] = [
            '--language', options.language,
            '--severity', options.severity || 'medium'
        ];

        // 一時ファイルに書き込んでレビュー
        const tmpFile = await this.writeTempFile(code, options.language);
        args.push(tmpFile);

        const output = await this.executeCli('review', args);
        return JSON.parse(output) as ReviewResult;
    }

    /**
     * テスト生成
     */
    async generateTests(
        code: string,
        options: TestGenOptions
    ): Promise<TestGenResult> {
        if (this.useHttp) {
            return this.callApi<TestGenResult>('/api/v1/testgen', {
                code,
                language: options.language,
                framework: options.framework || 'pytest',
                file_path: options.filePath
            });
        }

        // CLI使用
        const args: string[] = [
            '--language', options.language,
            '--framework', options.framework || 'pytest'
        ];

        const tmpFile = await this.writeTempFile(code, options.language);
        args.push(tmpFile);

        const output = await this.executeCli('testgen', args);
        return JSON.parse(output) as TestGenResult;
    }

    /**
     * バグ修正提案
     */
    async suggestFix(code: string, options: FixOptions): Promise<FixResult> {
        if (this.useHttp) {
            return this.callApi<FixResult>('/api/v1/fix', {
                code,
                language: options.language,
                error_description: options.errorDescription,
                file_path: options.filePath
            });
        }

        // CLI使用
        const args: string[] = [
            '--language', options.language
        ];

        if (options.errorDescription) {
            args.push('--error', options.errorDescription);
        }

        const tmpFile = await this.writeTempFile(code, options.language);
        args.push(tmpFile);

        const output = await this.executeCli('fix', args);
        return JSON.parse(output) as FixResult;
    }

    /**
     * 利用状況取得
     */
    async getUsage(): Promise<UsageInfo> {
        if (this.useHttp) {
            return this.callApi<UsageInfo>('/api/v1/usage', {});
        }

        // CLI使用
        const output = await this.executeCli('license', ['usage']);
        return JSON.parse(output) as UsageInfo;
    }

    /**
     * 一時ファイル作成
     */
    private async writeTempFile(
        content: string,
        language: string
    ): Promise<string> {
        const fs = await import('fs/promises');
        const os = await import('os');

        const ext = this.getExtension(language);
        const tmpDir = os.tmpdir();
        const tmpFile = path.join(tmpDir, `devbuddy_temp.${ext}`);

        await fs.writeFile(tmpFile, content, 'utf-8');
        return tmpFile;
    }

    /**
     * 言語から拡張子を取得
     */
    private getExtension(language: string): string {
        const extMap: Record<string, string> = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'rust': 'rs',
            'go': 'go'
        };
        return extMap[language] || 'txt';
    }
}
