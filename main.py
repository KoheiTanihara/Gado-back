import time
import os # os モジュールが必要
from fastapi import FastAPI, Depends, HTTPException # HTTPExceptionも追加すると良いかも
from fastapi.middleware.cors import CORSMiddleware  # CORSミドルウェアを追加
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
# from sqlalchemy.ext.declarative import declarative_base # models.py から Base を使うので不要

# models から Base と User をインポート (他のモデルもあれば同様に)
from app.models import Base, User
# from app.database import get_db # get_db は main.py 内で定義するので不要かも
from app.auth import router as auth_router, get_current_user
from app import tasks

# 環境変数からデータベースURLを取得
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/ptodo") # デフォルト値もあると良い

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- ここからが重要 ---

print("--- データベース接続待機 & テーブル作成 開始 ---")
# MySQLサーバーが起動するまで待機
max_retries = 10
retry_interval = 5
for attempt in range(max_retries):
    try:
        connection = engine.connect() # 実際に接続試行
        connection.close()
        print("--- データベース接続成功 ---")
        break # 接続成功したらループを抜ける
    except Exception as e:
        print(f"データベース接続を待機中 ({attempt + 1}/{max_retries}): {e}")
        if attempt + 1 == max_retries:
            print("--- 最大リトライ回数に達しました。データベース接続に失敗しました。---")
            # 必要であればここでアプリケーションを終了させる処理を追加
            exit() # または raise e など
        time.sleep(retry_interval)
else:
    # ループが break せずに終了した場合（通常は到達しないはず）
    print("--- データベース接続ループが予期せず終了しました ---")
    exit()


print("--- テーブル作成処理 開始 ---")
try:
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★ この行が実行される必要がある！ ★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    Base.metadata.create_all(bind=engine)
    print("--- テーブル作成処理 完了 ---") # これが表示されるはず！
except Exception as e:
    print(f"--- テーブル作成中にエラー発生: {e} ---")
    import traceback
    traceback.print_exc()
    # テーブル作成失敗は致命的なので終了させるか、エラーをraiseする
    exit()

# --- ここまでが重要 ---


print("--- FastAPI アプリケーションインスタンス化 ---")
app = FastAPI()

# CORSミドルウェアの設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境ではより制限的に設定することをお勧めします
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# get_db 関数を main.py 内で定義 (database.py にあるならそちらを import でもOK)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ルーターのインクルード
app.include_router(auth_router) # prefix は auth_router 側で定義済みのはず
app.include_router(tasks.router)

# ルートエンドポイントなど
@app.get("/")
async def read_root(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}

@app.get("/testdb")
async def test_db(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        db.execute(text("SELECT 1"))
        return {"message": f"Database connection successful. Hello {current_user.username}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# bcrypt エラーの対策 (もし行うなら)
# requirements.txt に `bcrypt==3.2.0` などを指定してバージョンを固定し、
# `docker-compose down -v && docker-compose up --build` で再構築する。