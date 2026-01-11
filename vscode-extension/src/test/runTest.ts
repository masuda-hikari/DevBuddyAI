/**
 * テストランナー
 * VSCode拡張テストを実行
 */

import * as path from 'path';
import { runTests } from '@vscode/test-electron';

async function main() {
    try {
        // 拡張機能のルートパス
        const extensionDevelopmentPath = path.resolve(__dirname, '../../');

        // テストスイートのパス
        const extensionTestsPath = path.resolve(__dirname, './suite/index');

        // テスト実行
        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            launchArgs: ['--disable-extensions']
        });
    } catch (err) {
        console.error('テスト実行に失敗しました');
        process.exit(1);
    }
}

main();
