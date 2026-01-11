/**
 * 問題一覧ツリービュープロバイダー
 * サイドバーに検出された問題を表示
 */

import * as vscode from 'vscode';
import { Issue } from '../client';

/**
 * 問題ツリーアイテム
 */
export class IssueTreeItem extends vscode.TreeItem {
    constructor(
        public readonly issue: Issue,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(issue.message, collapsibleState);

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
    private getIcon(severity: string): vscode.ThemeIcon {
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

/**
 * 問題一覧ツリービュープロバイダー
 */
export class IssueTreeProvider implements vscode.TreeDataProvider<IssueTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<IssueTreeItem | undefined | null | void> =
        new vscode.EventEmitter<IssueTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<IssueTreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private issues: Issue[] = [];

    constructor() {}

    /**
     * 問題一覧を更新
     */
    updateIssues(issues: Issue[]): void {
        this.issues = issues;
        this._onDidChangeTreeData.fire();
    }

    /**
     * 問題一覧をクリア
     */
    clearIssues(): void {
        this.issues = [];
        this._onDidChangeTreeData.fire();
    }

    /**
     * ツリーアイテムを取得
     */
    getTreeItem(element: IssueTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * 子要素を取得
     */
    getChildren(element?: IssueTreeItem): Thenable<IssueTreeItem[]> {
        if (element) {
            // 子要素がある場合（提案など）
            if (element.issue.suggestion) {
                return Promise.resolve([
                    new SuggestionTreeItem(element.issue.suggestion)
                ] as any);
            }
            return Promise.resolve([]);
        }

        // ルートレベル: 全問題を表示
        const items = this.issues.map(
            (issue) => new IssueTreeItem(
                issue,
                issue.suggestion
                    ? vscode.TreeItemCollapsibleState.Collapsed
                    : vscode.TreeItemCollapsibleState.None
            )
        );

        return Promise.resolve(items);
    }
}

/**
 * 提案ツリーアイテム
 */
class SuggestionTreeItem extends vscode.TreeItem {
    constructor(suggestion: string) {
        super(suggestion, vscode.TreeItemCollapsibleState.None);
        this.tooltip = suggestion;
        this.iconPath = new vscode.ThemeIcon('lightbulb');
    }
}
