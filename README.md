# 音楽推薦マップ (Recommend Map)

Spotifyのプレイリストから曲の特徴を分析し、2次元マップ上に可視化するWebアプリケーションです。さらに、選択した曲に基づいて類似曲を検索し、マップ上に表示することができます。

## 機能

- Spotifyのプレイリストから曲の特徴を取得
- 主成分分析（PCA）を用いた2次元マップへの可視化
- インタラクティブな曲の選択とジャケット画像表示
- 選択した曲に基づく類似曲の検索と表示
- 類似曲と元の曲との関連を線で表示

## 技術スタック

### バックエンド
- Python 3
- Flask (Webフレームワーク)
- Flask-Session (サーバーサイドセッション管理)
- Pandas, NumPy, Scikit-learn (データ分析、主成分分析)
- Spotipy (Spotify API クライアント)

### フロントエンド
- HTML5
- CSS3
- JavaScript
- Canvas API (2Dグラフィックス)

## セットアップ

### 必要条件
- Python 3.8以上
- Spotifyデベロッパーアカウント（APIキー取得用）

### インストール

1. リポジトリをクローン
```
git clone <リポジトリURL>
cd recommend-map
```

2. 依存関係のインストール
```
pip install -r requirements.txt
```

3. 環境変数の設定
`.env`ファイルを作成し、以下の内容を追加します：
```
FLAST_SECRET_KEY=<あなたのFlaskシークレットキー>
SPOTIPY_CLIENT_ID=<あなたのSpotify Client ID>
SPOTIPY_CLIENT_SECRET=<あなたのSpotify Client Secret>
```

### 起動方法

開発環境での起動:
```
python server.py
```

本番環境での起動:
```
gunicorn server:app
```

アプリケーションは `http://localhost:5000` でアクセスできます。

## 使い方

1. アプリケーションを起動し、トップページにアクセスします。
2. テキストフィールドにSpotifyのプレイリストIDを入力します。
   - プレイリストIDは `spotify:playlist:37i9dQZF1DXdurasRmJgpJ` のような形式です。
3. 必要に応じて「プレイリストを追加」ボタンでプレイリストを追加できます。
4. 「送信」ボタンをクリックして分析を開始します。
5. マップ上に表示された曲のジャケット画像をクリックすると、詳細情報がポップアップ表示されます。
6. 「類似曲を検索」ボタンをクリックすると、選択した曲に類似した曲が検索され、マップ上に追加表示されます。

## デプロイ

このアプリケーションはHerokuにデプロイできるよう設定されています。
`Procfile`が含まれており、Herokuの環境でgunicornを使用して起動します。

## ライセンス

[ライセンス情報をここに記載]

## 作者

[作者情報をここに記載]
