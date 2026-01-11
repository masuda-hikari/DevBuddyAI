/**
 * テストスイートエントリポイント
 */

import * as path from 'path';
import Mocha from 'mocha';
import { glob } from 'glob';

export function run(): Promise<void> {
    // Mochaインスタンス作成
    const mocha = new Mocha({
        ui: 'bdd',
        color: true,
        timeout: 60000
    });

    const testsRoot = path.resolve(__dirname, '.');

    return new Promise((resolve, reject) => {
        glob('**/**.test.js', { cwd: testsRoot }).then((files: string[]) => {
            // テストファイルを追加
            files.forEach((f: string) => mocha.addFile(path.resolve(testsRoot, f)));

            try {
                // テスト実行
                mocha.run((failures: number) => {
                    if (failures > 0) {
                        reject(new Error(`${failures}件のテストが失敗しました`));
                    } else {
                        resolve();
                    }
                });
            } catch (err) {
                console.error(err);
                reject(err);
            }
        }).catch((err: Error) => {
            return reject(err);
        });
    });
}
