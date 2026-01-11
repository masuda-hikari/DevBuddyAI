"use strict";
/**
 * VSCode診断管理
 * 検出された問題をエディタ上に表示
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
exports.DiagnosticManager = void 0;
const vscode = __importStar(require("vscode"));
/**
 * 診断管理クラス
 * DevBuddyAIが検出した問題をVSCodeの診断機能で表示
 */
class DiagnosticManager {
    diagnosticCollection;
    constructor() {
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('devbuddy');
    }
    /**
     * 診断コレクションを取得
     */
    getDiagnosticCollection() {
        return this.diagnosticCollection;
    }
    /**
     * 診断情報を更新
     */
    updateDiagnostics(uri, issues) {
        const diagnostics = issues.map((issue) => {
            const range = new vscode.Range(Math.max(0, issue.line - 1), issue.column ? issue.column - 1 : 0, Math.max(0, issue.line - 1), Number.MAX_VALUE);
            const severity = this.mapSeverity(issue.severity);
            const diagnostic = new vscode.Diagnostic(range, issue.message, severity);
            diagnostic.source = 'DevBuddyAI';
            diagnostic.code = issue.type;
            // 修正提案がある場合はrelatedInformationに追加
            if (issue.suggestion) {
                diagnostic.relatedInformation = [
                    new vscode.DiagnosticRelatedInformation(new vscode.Location(uri, range), `提案: ${issue.suggestion}`)
                ];
            }
            return diagnostic;
        });
        this.diagnosticCollection.set(uri, diagnostics);
    }
    /**
     * 診断情報をクリア
     */
    clearDiagnostics(uri) {
        if (uri) {
            this.diagnosticCollection.delete(uri);
        }
        else {
            this.diagnosticCollection.clear();
        }
    }
    /**
     * 重大度をマッピング
     */
    mapSeverity(severity) {
        switch (severity.toLowerCase()) {
            case 'error':
            case 'bug':
            case 'security':
                return vscode.DiagnosticSeverity.Error;
            case 'warning':
            case 'performance':
                return vscode.DiagnosticSeverity.Warning;
            case 'info':
            case 'style':
                return vscode.DiagnosticSeverity.Information;
            case 'hint':
                return vscode.DiagnosticSeverity.Hint;
            default:
                return vscode.DiagnosticSeverity.Information;
        }
    }
}
exports.DiagnosticManager = DiagnosticManager;
//# sourceMappingURL=diagnostics.js.map