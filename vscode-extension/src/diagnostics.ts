/**
 * VSCode診断管理
 * 検出された問題をエディタ上に表示
 */

import * as vscode from 'vscode';
import { Issue } from './client';

/**
 * 診断管理クラス
 * DevBuddyAIが検出した問題をVSCodeの診断機能で表示
 */
export class DiagnosticManager {
    private diagnosticCollection: vscode.DiagnosticCollection;

    constructor() {
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('devbuddy');
    }

    /**
     * 診断コレクションを取得
     */
    getDiagnosticCollection(): vscode.DiagnosticCollection {
        return this.diagnosticCollection;
    }

    /**
     * 診断情報を更新
     */
    updateDiagnostics(uri: vscode.Uri, issues: Issue[]): void {
        const diagnostics: vscode.Diagnostic[] = issues.map((issue) => {
            const range = new vscode.Range(
                Math.max(0, issue.line - 1),
                issue.column ? issue.column - 1 : 0,
                Math.max(0, issue.line - 1),
                Number.MAX_VALUE
            );

            const severity = this.mapSeverity(issue.severity);
            const diagnostic = new vscode.Diagnostic(range, issue.message, severity);

            diagnostic.source = 'DevBuddyAI';
            diagnostic.code = issue.type;

            // 修正提案がある場合はrelatedInformationに追加
            if (issue.suggestion) {
                diagnostic.relatedInformation = [
                    new vscode.DiagnosticRelatedInformation(
                        new vscode.Location(uri, range),
                        `提案: ${issue.suggestion}`
                    )
                ];
            }

            return diagnostic;
        });

        this.diagnosticCollection.set(uri, diagnostics);
    }

    /**
     * 診断情報をクリア
     */
    clearDiagnostics(uri?: vscode.Uri): void {
        if (uri) {
            this.diagnosticCollection.delete(uri);
        } else {
            this.diagnosticCollection.clear();
        }
    }

    /**
     * 重大度をマッピング
     */
    private mapSeverity(severity: string): vscode.DiagnosticSeverity {
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
