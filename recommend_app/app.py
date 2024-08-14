from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
import warnings
import os
import pickle
import json


## 分析系
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sklearn
from sklearn.decomposition import PCA

## 保存・API系
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)

## サーバーサイドセッションの設定を追加
app.config['SESSION_TYPE'] = 'filesystem'  # ファイルシステムにセッションを保存
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')  # セッションファイルの保存先ディレクトリ
app.config['SESSION_PERMANENT'] = False  # セッションを永続化するかどうか
app.config['SESSION_USE_SIGNER'] = True  # セッションIDを署名して保護する

## Flask-Sessionの初期化
Session(app)

## APIキーの取得
load_dotenv()
app.secret_key = os.getenv('FLAST_SECRET_KEY')
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

## SpotifyAPIの認証
client_credentials_manager = SpotifyClientCredentials(
    client_id = SPOTIPY_CLIENT_ID,
    client_secret = SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

## 使用する変数
trackInfos = [
    'id',
    'name'
]

artistInfos = [
    'id',
    'name'
]

trackImages = [
    'url'
]

useParams = [
    'acousticness',
    'danceability',
    'energy',
    'instrumentalness',
    'liveness',
    'speechiness',
    'tempo',
    'valence'
]

columns_trackInfos = ['track_' + useTrackInfo for useTrackInfo in trackInfos]
columns_artistInfos = ['artist_' + useArtistInfo for useArtistInfo in artistInfos]

columns = columns_trackInfos + columns_artistInfos + trackImages + useParams

"""
'spotify:playlist:37i9dQZF1DXdurasRmJgpJ', ## 令和ポップス
'spotify:playlist:37i9dQZF1DX4OR8pnFkwhR',  ## RADAR
'spotify:playlist:37i9dQZF1DX9ww9tisjowN'  ## Gacha Pop
"""

## プレイリスト内のトラックを取得する関数
def getPlaylist(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

## 各プレイリスト内のトラックを取得する関数
def getPlaylistsTracks(playlist_ids):
    all_tracks = []
    for playlist_id in playlist_ids:
        tracks = getPlaylist(playlist_id)
        all_tracks.append(tracks)
    return all_tracks

## ローカルに保存済みの特徴データを取得する関数
def loadPickle(filename):
    try:
        with open(filename, 'rb') as f:
            """
            a = pickle.load(f)
            print(filename, "を読み込みました。", flush=True)
            return a
            """
            return []
    except Exception as e:
        print("ファイルの中身が空です。", flush=True)
        return []

def loadPickles(n):
    _datas = []
    for index in range(n):
        _datas.append(loadPickle('data' + str(index) + '.pkl'))
    return _datas

## APIから各トラックの特徴データを取得する関数
def saveAudioFeatures(all_tracks, datas):
    global trackInfos, artistInfos, trackImages, useParams
    for index, data in enumerate(datas):
        tracks = all_tracks[index]
        if data == []:
            track_ids = [song['track']['id'] for song in tracks]

            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                audio_features = sp.audio_features(batch)

                for j, af in enumerate(audio_features):
                    song = tracks[i+j]['track']

                    _list = [song[infoName] for infoName in trackInfos]
                    _list += [song['artists'][0][infoName] for infoName in artistInfos]
                    _list += [song['album']['images'][0][name] for name in trackImages]
                    _list += [af[paramName] for paramName in useParams]

                    data.append(_list)

## 標準化する関数
def StandardScaler(_df, _mean, _std):
    _df = _df.to_numpy()
    _df_scaled = []
    for i in _df:
        _df_scaled.append(
            (i - _mean) / _std
        )
    return _df_scaled

## 関連曲を取得する関数
def getRecommendations(_df_id, _df_transformed, i):
    global columns, useParams

    ## シード曲の情報
    seed_track_id = [_df_id['track_id'].iloc[i]]
    seed_track_name = [_df_id['track_name'].iloc[i]]
    seed_artist_id = [_df_id['artist_id'].iloc[i]]
    seed_params = [_df_id[param].iloc[i] for param in useParams]

    ## 閾値
    thresold = 0.1
    ## 特徴データの閾値を設定
    max_params = []
    min_params = []

    loudness_threshold = 60
    tempo_threshold = 150

    for i, seed_param in enumerate(seed_params):
        if useParams[i] == 'loudness':
            max_params.append(seed_param + loudness_threshold * thresold)
            min_params.append(seed_param - loudness_threshold * thresold)
        elif useParams[i] == 'tempo':
            max_params.append(seed_param + 150 * thresold)
            min_params.append(seed_param - 150 * thresold)
        else:
            max_params.append(seed_param + thresold)
            min_params.append(seed_param - thresold)

    ## 関連曲を取得
    params = {
        'seed_tracks': seed_track_id,
        'seed_artists': seed_artist_id,
        'limit': 5
    }

    for i, paramName in enumerate(useParams):
        params['max_' + paramName] = max_params[i]
        params['min_' + paramName] = min_params[i]

    print("取得前", flush=True)

    _recommendations = sp.recommendations(**params)

    print("取得後", flush=True)

    ## 関連曲がシード曲と一致していた場合は削除
    _recommendations_tracks = [
        track for track in _recommendations['tracks']
        if track['name'] not in _df_id.track_name and track['name'] not in seed_track_name
    ]

    track_ids = [track['id'] for track in _recommendations_tracks]
    track_names = [track['name'] for track in _recommendations_tracks]

    ## 関連曲の特徴データを取得
    if track_ids == []:
        print(seed_track_name, "の関連曲はありません。", flush=True)
        return []
    else:
        print(seed_track_name, "の関連曲は", track_names, flush=True)
        _audio_features = sp.audio_features(track_ids)

        _addData = []
        for j, af in enumerate(_audio_features):
            song = _recommendations_tracks[j]

            _list = [song[info] for info in trackInfos]
            _list += [song['artists'][0][info] for info in artistInfos]
            _list += [song['album']['images'][0][name] for name in trackImages]
            _list += [af[param] for param in useParams]

            _addData.append(_list)

        return _addData

## プレイリストIDの取得
@app.route('/playlist_id', methods=['POST'])
def getPlaylistId():
    global columns

    playlist_ids = request.json
    session['playlist_ids'] = playlist_ids

    # 各ユーザーごとのデータフレームと分析データをセッションに保存
    session['df_id'] = pd.DataFrame(columns=columns).to_dict()
    session['df_scaled'] = []
    session['df_transformed'] = []
    session['mean'] = []
    session['std'] = []

    ## 各プレイリスト内のトラックを取得
    all_tracks = getPlaylistsTracks(playlist_ids)

    ## ローカルに保存済みの特徴データを取得
    datas = []
    for index in range(len(all_tracks)):
        data = loadPickle('data' + str(index) + '.pkl')
        datas.append(data)

    ## APIから各トラックの特徴データを取得
    saveAudioFeatures(all_tracks, datas)

    ## データフレームに変換
    dfList = []
    for i, data in enumerate(datas):
        df = pd.DataFrame(data = data, index = None, columns = columns)
        dfList.append(df)
        dfList[i]['UserId'] = i+1
        dfList[i]['recommendId'] = -1

    ## データフレームを連結
    df_id = pd.DataFrame(columns = columns)
    for _df_transformed in dfList:
        df_id = pd.concat([df_id, _df_transformed])

    df_id = df_id.reset_index(drop = True)
    session['df_id'] = df_id.to_dict()

    ## 数値以外を削除
    df = df_id.iloc[:, len(trackInfos)+len(artistInfos)+len(trackImages):len(columns)-1]

    ## 標準化
    mean = np.mean(df, axis=0)
    std = np.std(df, axis=0)

    df_scaled = StandardScaler(df, mean, std)
    df_scaled = pd.DataFrame(
        data = df_scaled,
        index = None,
        columns = columns[len(trackInfos)+len(artistInfos)+len(trackImages):len(columns)-1]
    )
    session['df_scaled'] = df_scaled.values.tolist()

    ## 主成分分析
    pca = PCA(n_components = 2)
    pca.fit(df_scaled)
    df_transformed = pca.transform(df_scaled)

    session['df_transformed'] = df_transformed.tolist()
    session['mean'] = mean.tolist()
    session['std'] = std.tolist()

    return {
        'result': 'success'
    }

## 類似曲の取得をJavaScriptから実行
@app.route('/run_function', methods=['POST'])
def run_function():
    i = request.json

    df_id = pd.DataFrame(session['df_id'])
    df_scaled = np.array(session['df_scaled'])
    df_transformed = np.array(session['df_transformed'])
    mean = np.array(session['mean'])
    std = np.array(session['std'])

    # PCAモデルの再構築
    pca = PCA(n_components = 2)
    pca.fit(df_scaled)

    ## クリックイベント
    def onClick(i, df_transformed, df_id, mean, std, pca):
        print("クリックされました。", flush=True)

        ## レコメンドデータを取得
        _addData = getRecommendations(df_id, df_transformed, i)

        if _addData != []:
            ## データフレームに変換
            df_add_id = pd.DataFrame(data = _addData, index = None, columns = columns)
            df_add_id['UserId'] = 0
            df_add_id['recommendId'] = i

            ## レコメンドデータを追加
            df_id = pd.concat([df_id, df_add_id])
            df_id = df_id.reset_index()
            df_id = df_id.drop('index', axis = 1)

            ## 数値以外を削除
            df_add = df_add_id.iloc[:, len(trackInfos)+len(artistInfos)+len(trackImages):len(columns)-1]

            ## 標準化
            df_add_scaled = StandardScaler(df_add, mean, std)
            df_add_scaled = pd.DataFrame(
                data = df_add_scaled,
                index = None,
                columns = columns[len(trackInfos)+len(artistInfos)+len(trackImages):len(columns)-1]
            )

            ## 主成分分析
            df_add_transformed = pca.transform(df_add_scaled)

            ## レコメンドデータを追加
            df_transformed = np.vstack((df_transformed, df_add_transformed))

            df_id = df_id.reset_index()
            df_id = df_id.drop('index', axis = 1)

            # 更新されたデータをセッションに保存
            session['df_id'] = df_id.to_dict()
            session['df_transformed'] = df_transformed.tolist()
            print("df_transformed saved in session:", session.get('df_transformed'), flush=True)

        return {
            'result': 'success'
        }

    result = onClick(i, df_transformed, df_id, mean, std, pca)

    # 結果をクライアントに返す
    return jsonify(result)

# 情報をJSON形式でJavascriptに送る
@app.route('/data')
def get_data():
    df_transformed = pd.DataFrame(session['df_transformed'], columns=['x', 'y'])
    df_id = pd.DataFrame(session['df_id'])

    response = {
        'transformed': df_transformed.to_dict(orient='records'),
        'id': df_id.to_dict(orient='records')
    }

    return jsonify(response)

@app.route('/')
def index():
    return render_template('recommend_app/index.html')