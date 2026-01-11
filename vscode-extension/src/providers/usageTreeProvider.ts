/**
 * 利用状況ツリービュープロバイダー
 * サイドバーに利用状況を表示
 */

import * as vscode from 'vscode';
import { DevBuddyClient, UsageInfo } from '../client';

/**
 * 利用状況ツリーアイテム
 */
export class UsageTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly description: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly iconPath?: vscode.ThemeIcon
    ) {
        super(label, collapsibleState);
        this.description = description;
    }
}

/**
 * 利用状況ツリービュープロバイダー
 */
export class UsageTreeProvider implements vscode.TreeDataProvider<UsageTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<UsageTreeItem | undefined | null | void> =
        new vscode.EventEmitter<UsageTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<UsageTreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private usage: UsageInfo | null = null;
    private client: DevBuddyClient;

    constructor(client: DevBuddyClient) {
        this.client = client;
    }

    /**
     * 利用状況を更新
     */
    async refreshUsage(): Promise<void> {
        try {
            this.usage = await this.client.getUsage();
            this._onDidChangeTreeData.fire();
        } catch (error) {
            console.error('利用状況取得エラー:', error);
            this.usage = null;
            this._onDidChangeTreeData.fire();
        }
    }

    /**
     * ツリーアイテムを取得
     */
    getTreeItem(element: UsageTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * 子要素を取得
     */
    getChildren(element?: UsageTreeItem): Thenable<UsageTreeItem[]> {
        if (element) {
            return Promise.resolve([]);
        }

        if (!this.usage) {
            return Promise.resolve([
                new UsageTreeItem(
                    '利用状況を取得',
                    'クリックして更新',
                    vscode.TreeItemCollapsibleState.None,
                    new vscode.ThemeIcon('refresh')
                )
            ]);
        }

        const items: UsageTreeItem[] = [
            new UsageTreeItem(
                'プラン',
                this.usage.plan,
                vscode.TreeItemCollapsibleState.None,
                new vscode.ThemeIcon('account')
            ),
            new UsageTreeItem(
                'レビュー',
                `${this.usage.reviews.used} / ${this.usage.reviews.limit}`,
                vscode.TreeItemCollapsibleState.None,
                this.getUsageIcon(this.usage.reviews.used, this.usage.reviews.limit)
            ),
            new UsageTreeItem(
                'テスト生成',
                `${this.usage.testgen.used} / ${this.usage.testgen.limit}`,
                vscode.TreeItemCollapsibleState.None,
                this.getUsageIcon(this.usage.testgen.used, this.usage.testgen.limit)
            ),
            new UsageTreeItem(
                '修正提案',
                `${this.usage.fixes.used} / ${this.usage.fixes.limit}`,
                vscode.TreeItemCollapsibleState.None,
                this.getUsageIcon(this.usage.fixes.used, this.usage.fixes.limit)
            ),
            new UsageTreeItem(
                'リセット日',
                this.usage.resetDate,
                vscode.TreeItemCollapsibleState.None,
                new vscode.ThemeIcon('calendar')
            )
        ];

        return Promise.resolve(items);
    }

    /**
     * 利用率に応じたアイコンを取得
     */
    private getUsageIcon(used: number, limit: number): vscode.ThemeIcon {
        const ratio = used / limit;

        if (ratio >= 0.9) {
            return new vscode.ThemeIcon('warning', new vscode.ThemeColor('errorForeground'));
        } else if (ratio >= 0.7) {
            return new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('editorWarning.foreground'));
        } else {
            return new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('charts.green'));
        }
    }
}
