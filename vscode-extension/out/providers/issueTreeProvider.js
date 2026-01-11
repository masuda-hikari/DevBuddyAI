"use strict";
/**
 * 問題一覧ツリービュープロバイダー
 * サイドバーに検出された問題を表示
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
exports.IssueTreeProvider = exports.IssueTreeItem = void 0;
const vscode = __importStar(require("vscode"));
/**
 * 問題ツリーアイテム
 */
class IssueTreeItem extends vscode.TreeItem {
    issue;
    collapsibleState;
    constructor(issue, collapsibleState) {
        super(issue.message, collapsibleState);
        this.issue = issue;
        this.collapsibleState = collapsibleState;
        this.tooltip = `${issue.type}: ${issue.message}\n行 ${issue.line}`;
        this.description = `行 ${issue.line}`;
        // アイコン設定
        this.iconPath = this.getIcon(issue.severity);
        // クリック時にその行にジャンプ
        this.command = {
            command: 'devbuddy.goToIssue',
            title: '問題箇所へ移動',
            arguments: [issue]
        };
    }
    /**
     * 重大度に応じたアイコンを取得
     */
    getIcon(severity) {
        switch (severity.toLowerCase()) {
            case 'error':
            case 'bug':
            case 'security':
                return new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
            case 'warning':
            case 'performance':
                return new vscode.ThemeIcon('warning', new vscode.ThemeColor('editorWarning.foreground'));
            case 'info':
            case 'style':
                return new vscode.ThemeIcon('info', new vscode.ThemeColor('editorInfo.foreground'));
            default:
                return new vscode.ThemeIcon('circle-outline');
        }
    }
}
exports.IssueTreeItem = IssueTreeItem;
/**
 * 問題一覧ツリービュープロバイダー
 */
class IssueTreeProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    issues = [];
    constructor() { }
    /**
     * 問題一覧を更新
     */
    updateIssues(issues) {
        this.issues = issues;
        this._onDidChangeTreeData.fire();
    }
    /**
     * 問題一覧をクリア
     */
    clearIssues() {
        this.issues = [];
        this._onDidChangeTreeData.fire();
    }
    /**
     * ツリーアイテムを取得
     */
    getTreeItem(element) {
        return element;
    }
    /**
     * 子要素を取得
     */
    getChildren(element) {
        if (element) {
            // 子要素がある場合（提案など）
            if (element.issue.suggestion) {
                return Promise.resolve([
                    new SuggestionTreeItem(element.issue.suggestion)
                ]);
            }
            return Promise.resolve([]);
        }
        // ルートレベル: 全問題を表示
        const items = this.issues.map((issue) => new IssueTreeItem(issue, issue.suggestion
            ? vscode.TreeItemCollapsibleState.Collapsed
            : vscode.TreeItemCollapsibleState.None));
        return Promise.resolve(items);
    }
}
exports.IssueTreeProvider = IssueTreeProvider;
/**
 * 提案ツリーアイテム
 */
class SuggestionTreeItem extends vscode.TreeItem {
    constructor(suggestion) {
        super(suggestion, vscode.TreeItemCollapsibleState.None);
        this.tooltip = suggestion;
        this.iconPath = new vscode.ThemeIcon('lightbulb');
    }
}
//# sourceMappingURL=issueTreeProvider.js.map