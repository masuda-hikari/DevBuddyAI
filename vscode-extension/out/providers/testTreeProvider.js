"use strict";
/**
 * 生成テストツリービュープロバイダー
 * サイドバーに生成されたテストを表示
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
exports.TestTreeProvider = exports.TestTreeItem = void 0;
const vscode = __importStar(require("vscode"));
/**
 * テストツリーアイテム
 */
class TestTreeItem extends vscode.TreeItem {
    test;
    collapsibleState;
    constructor(test, collapsibleState) {
        super(test.name, collapsibleState);
        this.test = test;
        this.collapsibleState = collapsibleState;
        this.tooltip = test.description;
        this.description = test.description;
        this.iconPath = new vscode.ThemeIcon('beaker');
    }
}
exports.TestTreeItem = TestTreeItem;
/**
 * 生成テストツリービュープロバイダー
 */
class TestTreeProvider {
    _onDidChangeTreeData = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChangeTreeData.event;
    tests = [];
    constructor() { }
    /**
     * テスト一覧を更新
     */
    updateTests(tests) {
        this.tests = tests;
        this._onDidChangeTreeData.fire();
    }
    /**
     * テスト一覧をクリア
     */
    clearTests() {
        this.tests = [];
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
            return Promise.resolve([]);
        }
        // ルートレベル: 全テストを表示
        const items = this.tests.map((test) => new TestTreeItem(test, vscode.TreeItemCollapsibleState.None));
        return Promise.resolve(items);
    }
}
exports.TestTreeProvider = TestTreeProvider;
//# sourceMappingURL=testTreeProvider.js.map