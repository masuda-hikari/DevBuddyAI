"""
Web APIサーバーのサンプルコード（FastAPI）

このコードをDevBuddyAIでレビュー・テスト生成してみましょう：
$ devbuddy review samples/web_api_server.py
$ devbuddy testgen samples/web_api_server.py
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

app = FastAPI()


class User(BaseModel):
    """ユーザーモデル"""
    id: Optional[int] = None
    name: str
    email: str
    age: int


class UserRepository:
    """ユーザーリポジトリ（データベース操作）"""

    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def create_user(self, user: User) -> User:
        """ユーザー作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                (user.name, user.email, user.age)
            )
            conn.commit()
            user.id = cursor.lastrowid
            return user
        except sqlite3.IntegrityError:
            raise ValueError(f"Email {user.email} already exists")
        finally:
            conn.close()

    def get_user(self, user_id: int) -> Optional[User]:
        """ユーザー取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return User(id=row[0], name=row[1], email=row[2], age=row[3])
        return None

    def list_users(self) -> List[User]:
        """全ユーザー取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()

        return [User(id=r[0], name=r[1], email=r[2], age=r[3]) for r in rows]

    def delete_user(self, user_id: int) -> bool:
        """ユーザー削除"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted


# グローバルリポジトリインスタンス
repo = UserRepository()


@app.post("/users", response_model=User)
async def create_user(user: User):
    """ユーザー作成エンドポイント"""
    try:
        return repo.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """ユーザー取得エンドポイント"""
    user = repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users", response_model=List[User])
async def list_users():
    """全ユーザー取得エンドポイント"""
    return repo.list_users()


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """ユーザー削除エンドポイント"""
    deleted = repo.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# DevBuddyAIで検出される可能性のある問題：
# - SQLインジェクション対策（このコードはパラメータ化されているのでOK）
# - データベース接続のリソースリーク（毎回close()しているのでOK）
# - エラーハンドリング（try-exceptあり）
# - 型ヒント（すべて適切に設定）
#
# DevBuddyAIが生成するテストの例：
# - 正常系: ユーザー作成・取得・削除
# - 異常系: 重複email、存在しないID、無効な入力
# - エッジケース: 空のリスト、境界値（age=0, age=150）
