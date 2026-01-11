/**
 * 生成テストツリービュープロバイダー
 * サイドバーに生成されたテストを表示
 */

import * as vscode from 'vscode';
import { TestInfo } from '../client';

/**
 * テストツリーアイテム
 */
export class TestTreeItem extends vscode.TreeItem {
    constructor(
        public readonly test: TestInfo,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(test.name, collapsibleState);

        this.tooltip = test.description;
        this.description = test.description;
        this.iconPath = new vscode.ThemeIcon('beaker');
    }
}

/**
 * 生成テストツリービュープロバイダー
 */
export class TestTreeProvider implements vscode.TreeDataProvider<TestTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<TestTreeItem | undefined | null | void> =
        new vscode.EventEmitter<TestTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<TestTreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private tests: TestInfo[] = [];

    constructor() {}

    /**
     * テスト一覧を更新
     */
    updateTests(tests: TestInfo[]): void {
        this.tests = tests;
        this._onDidChangeTreeData.fire();
    }

    /**
     * テスト一覧をクリア
     */
    clearTests(): void {
        this.tests = [];
        this._onDidChangeTreeData.fire();
    }

    /**
     * ツリーアイテムを取得
     */
    getTreeItem(element: TestTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * 子要素を取得
     */
    getChildren(element?: TestTreeItem): Thenable<TestTreeItem[]> {
        if (element) {
            return Promise.resolve([]);
        }

        // ルートレベル: 全テストを表示
        const items = this.tests.map(
            (test) => new TestTreeItem(test, vscode.TreeItemCollapsibleState.None)
        );

        return Promise.resolve(items);
    }
}
