"use strict";
/**
 * 利用状況ツリービュープロバイダー
 * サイドバーに利用状況を表示
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
exports.UsageTreeProvider = exports.UsageTreeItem = void 0;
const vscode = __importStar(require("vscode"));
/**
 * 利用状況ツリーアイテム
 */
class UsageTreeItem extends vscode.TreeItem {
    label;
    description;
    collapsibleState;
    iconPath;
    constructor(label, description, collapsibleState, iconPath) {
        super(label, collapsibleState);
        this.label = label;
        this.description = description;
        this.collapsibleState = collapsibleState;
        this.iconPath = iconPath;
        this.description = description;
    }
}
exports.UsageTreeItem = UsageTreeItem;
/**
 * 利用状況ツリービュープロバイダー
 */
class UsageTreeProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    usage = null;
    client;
    constructor(client) {
        this.client = client;
    }
    /**
     * 利用状況を更新
     */
    async refreshUsage() {
        try {
            this.usage = await this.client.getUsage();
            this._onDidChangeTreeData.fire();
        }
        catch (error) {
            console.error('利用状況取得エラー:', error);
            this.usage = null;
            this._onDidChangeTreeData.fire();
        }
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
            return Promise.resolve([]);
        }
        if (!this.usage) {
            return Promise.resolve([
                new UsageTreeItem('利用状況を取得', 'クリックして更新', vscode.TreeItemCollapsibleState.None, new vscode.ThemeIcon('refresh'))
            ]);
        }
        const items = [
            new UsageTreeItem('プラン', this.usage.plan, vscode.TreeItemCollapsibleState.None, new vscode.ThemeIcon('account')),
            new UsageTreeItem('レビュー', `${this.usage.reviews.used} / ${this.usage.reviews.limit}`, vscode.TreeItemCollapsibleState.None, this.getUsageIcon(this.usage.reviews.used, this.usage.reviews.limit)),
            new UsageTreeItem('テスト生成', `${this.usage.testgen.used} / ${this.usage.testgen.limit}`, vscode.TreeItemCollapsibleState.None, this.getUsageIcon(this.usage.testgen.used, this.usage.testgen.limit)),
            new UsageTreeItem('修正提案', `${this.usage.fixes.used} / ${this.usage.fixes.limit}`, vscode.TreeItemCollapsibleState.None, this.getUsageIcon(this.usage.fixes.used, this.usage.fixes.limit)),
            new UsageTreeItem('リセット日', this.usage.resetDate, vscode.TreeItemCollapsibleState.None, new vscode.ThemeIcon('calendar'))
        ];
        return Promise.resolve(items);
    }
    /**
     * 利用率に応じたアイコンを取得
     */
    getUsageIcon(used, limit) {
        const ratio = used / limit;
        if (ratio >= 0.9) {
            return new vscode.ThemeIcon('warning', new vscode.ThemeColor('errorForeground'));
        }
        else if (ratio >= 0.7) {
            return new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('editorWarning.foreground'));
        }
        else {
            return new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('charts.green'));
        }
    }
}
exports.UsageTreeProvider = UsageTreeProvider;
//# sourceMappingURL=usageTreeProvider.js.map