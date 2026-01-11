"use strict";
/**
 * DevBuddyAI APIクライアント
 * CLI/サーバーとの通信を担当
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DevBuddyClient = void 0;
const vscode = __importStar(require("vscode"));
const axios_1 = __importStar(require("axios"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
/**
 * DevBuddyAIクライアント
 * CLIまたはHTTP APIを使用してDevBuddyAIサービスと通信
 */
class DevBuddyClient {
    httpClient = null;
    useHttp = false;
    constructor() {
        this.initializeClient();
    }
    /**
     * クライアント初期化
     */
    initializeClient() {
        const config = vscode.workspace.getConfiguration('devbuddy');
        const serverUrl = config.get('serverUrl');
        if (serverUrl) {
            this.useHttp = true;
            this.httpClient = axios_1.default.create({
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
    getApiKey() {
        const config = vscode.workspace.getConfiguration('devbuddy');
        const apiKey = config.get('apiKey') || process.env.DEVBUDDY_API_KEY;
        if (!apiKey) {
            throw new Error('API key not configured');
        }
        return apiKey;
    }
    /**
     * CLI実行
     */
    async executeCli(command, args, input) {
        return new Promise((resolve, reject) => {
            const config = vscode.workspace.getConfiguration('devbuddy');
            const cliPath = config.get('cliPath') || 'devbuddy';
            const fullArgs = [command, ...args, '--format', 'json'];
            const proc = (0, child_process_1.spawn)(cliPath, fullArgs, {
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
                }
                else {
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
    async callApi(endpoint, data) {
        if (!this.httpClient) {
            throw new Error('HTTP client not initialized');
        }
        try {
            const response = await this.httpClient.post(endpoint, data, {
                headers: {
                    'Authorization': `Bearer ${this.getApiKey()}`
                }
            });
            return response.data;
        }
        catch (error) {
            if (error instanceof axios_1.AxiosError) {
                if (error.response?.status === 401) {
                    throw new Error('API key invalid');
                }
                else if (error.response?.status === 429) {
                    throw new Error('rate limit exceeded');
                }
                else if (error.code === 'ECONNREFUSED') {
                    throw new Error('network error: server not reachable');
                }
                throw new Error(error.response?.data?.detail || error.message);
            }
            throw error;
        }
    }
    /**
     * コードレビュー
     */
    async review(code, options) {
        if (this.useHttp) {
            return this.callApi('/api/v1/review', {
                code,
                language: options.language,
                severity: options.severity || 'medium',
                file_path: options.filePath
            });
        }
        // CLI使用
        const args = [
            '--language', options.language,
            '--severity', options.severity || 'medium'
        ];
        // 一時ファイルに書き込んでレビュー
        const tmpFile = await this.writeTempFile(code, options.language);
        args.push(tmpFile);
        const output = await this.executeCli('review', args);
        return JSON.parse(output);
    }
    /**
     * テスト生成
     */
    async generateTests(code, options) {
        if (this.useHttp) {
            return this.callApi('/api/v1/testgen', {
                code,
                language: options.language,
                framework: options.framework || 'pytest',
                file_path: options.filePath
            });
        }
        // CLI使用
        const args = [
            '--language', options.language,
            '--framework', options.framework || 'pytest'
        ];
        const tmpFile = await this.writeTempFile(code, options.language);
        args.push(tmpFile);
        const output = await this.executeCli('testgen', args);
        return JSON.parse(output);
    }
    /**
     * バグ修正提案
     */
    async suggestFix(code, options) {
        if (this.useHttp) {
            return this.callApi('/api/v1/fix', {
                code,
                language: options.language,
                error_description: options.errorDescription,
                file_path: options.filePath
            });
        }
        // CLI使用
        const args = [
            '--language', options.language
        ];
        if (options.errorDescription) {
            args.push('--error', options.errorDescription);
        }
        const tmpFile = await this.writeTempFile(code, options.language);
        args.push(tmpFile);
        const output = await this.executeCli('fix', args);
        return JSON.parse(output);
    }
    /**
     * 利用状況取得
     */
    async getUsage() {
        if (this.useHttp) {
            return this.callApi('/api/v1/usage', {});
        }
        // CLI使用
        const output = await this.executeCli('license', ['usage']);
        return JSON.parse(output);
    }
    /**
     * 一時ファイル作成
     */
    async writeTempFile(content, language) {
        const fs = await Promise.resolve().then(() => __importStar(require('fs/promises')));
        const os = await Promise.resolve().then(() => __importStar(require('os')));
        const ext = this.getExtension(language);
        const tmpDir = os.tmpdir();
        const tmpFile = path.join(tmpDir, `devbuddy_temp.${ext}`);
        await fs.writeFile(tmpFile, content, 'utf-8');
        return tmpFile;
    }
    /**
     * 言語から拡張子を取得
     */
    getExtension(language) {
        const extMap = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'rust': 'rs',
            'go': 'go'
        };
        return extMap[language] || 'txt';
    }
}
exports.DevBuddyClient = DevBuddyClient;
//# sourceMappingURL=client.js.map