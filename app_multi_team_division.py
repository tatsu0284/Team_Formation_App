import streamlit as st
import pandas as pd
import random
import statistics

# --- カスタムCSS（既存のものを維持） ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0px !important; }
    div.stButton > button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- ページ設定 ---
st.set_page_config(page_title="チーム編成アプリ", layout="wide")

# --- 履歴管理用のセッション状態 ---
if "pair_history" not in st.session_state:
    # 過去に同じチームになったペアを記録する辞書 {(名前A, 名前B): 回数}
    st.session_state.pair_history = {}

def solve_multi_team_division(member_df, num_per_team, iterations=10000):

    # members = dict(zip(member_df["名前"], member_df["身長"]))
    # インデックスを振り直して、名前と身長を確実にペアリングする
    df_clean = member_df.reset_index(drop=True)
    # df.index = pd.Series(df.index).apply(lambda x:x+1) # インデックスを1から始める
    members = dict(zip(df_clean["名前"], df_clean["身長"]))    
    member_names = list(members.keys())
    total_members = len(member_names)
    
    num_teams = total_members // num_per_team
    active_member_count = num_teams * num_per_team
    
    if num_teams < 2:
        # return None, f"エラー: 2チーム以上作るには4名以上の登録が必要です。"
        return None, f"エラー: 2チーム以上作るには{num_per_team * 2}名以上の登録が必要です。"
    
    best_score = float('inf')
    best_assignment = None

    # 履歴ペアへのペナルティの重み（この値を大きくすると、身長差より「初対面」を優先します）
    PENALTY_WEIGHT = 5.0 

    for _ in range(iterations):
        selected_members = random.sample(member_names, active_member_count)
        current_teams = []
        penalty = 0
        
        for i in range(num_teams):
            team = selected_members[i * num_per_team : (i + 1) * num_per_team]
            current_teams.append(team)
            
            # 同じチーム内でのペア重複をチェック
            for pair in itertools.combinations(sorted(team), 2):
                if pair in st.session_state.pair_history:
                    # 過去に一緒になった回数分だけペナルティを加算
                    penalty += st.session_state.pair_history[pair] * PENALTY_WEIGHT

        # 身長のバラつき（標準偏差）を計算
        averages = [sum(members[m] for m in team) / num_per_team for team in current_teams]
        height_score = statistics.stdev(averages)
        
        # 最終スコア = 身長のバラつき + 重複ペナルティ
        total_score = height_score + penalty
        
        if total_score < best_score:
            best_score = total_score
            best_assignment = (current_teams, averages)
            if total_score == 0: break

    return best_assignment, None

import itertools # ペア抽出用に追加

# --- UI部分 ---
st.markdown('<h4>🏃‍♂️ チーム編成アプリ</h4>', unsafe_allow_html=True)
st.write("メンバーの名前と身長を入力してください（4名〜）。")

# 履歴のリセットボタン
# if st.sidebar.button("対戦履歴をリセット"):
#     st.session_state.pair_history = {}
#     st.sidebar.success("履歴をクリアしました。")
# サイドバー設定
with st.sidebar:
    st.header("設定")
    if st.button("対戦履歴をリセット"):
        st.session_state.pair_history = {}
        st.success("履歴をクリアしました。")
    st.write(f"現在の記録ペア数: {len(st.session_state.pair_history)}")

# 初期データの作成
if "df" not in st.session_state:
    initial_data = [
            {"名前": "さなちゃん", "身長": 170}, 
            {"名前": "ごう",       "身長": 165},
            {"名前": "りく",       "身長": 165}, 
            {"名前": "ゆうだい",   "身長": 165},
            {"名前": "ゆりりん",   "身長": 155}, 
            {"名前": "ゆうあ",     "身長": 155},
            {"名前": "しりゅう",   "身長": 155}, 
            {"名前": "あいな",     "身長": 140},
            {"名前": "わっくん",   "身長": 155}, 
            {"名前": "そうちゃん", "身長": 150},
            {"名前": "ゆきちゃん", "身長": 135}, 
            {"名前": "みきちゃん", "身長": 130},
            {"名前": "こっとん",   "身長": 140},
        ]
    df = pd.DataFrame(initial_data)
    # 明示的に1からの連番をIndexに設定
    df.index = range(1, len(df) + 1)
    # df = df.reset_index(drop=False)
    st.session_state.df = df

# 1. 編集可能なテーブル
edited_df = st.data_editor(
    st.session_state.df,
    num_rows = "dynamic", # 行の追加・削除を可能に
    # use_container_width = False,
    width = 300, # テーブルの幅を固定
    column_config = {
        "名前": st.column_config.TextColumn("名前", required=True),
        "身長": st.column_config.NumberColumn("身長 (cm)", format="%.0f", min_value=100, max_value=200),
    },
    # 常に全行が見えるようテーブル高さを計算
    # height = 530,
    # height = int(len(st.session_state.df)*41),
    height = int((len(st.session_state.df) + 0) * 41), # 動的な高さ調整
)
# st.session_state.df = edited_df
# 【重要】インデックスの自動補完ロジック
# 編集・追加されたデータをクリーンアップしてセッションに戻す
if not edited_df.equals(st.session_state.df):
    # 有効なデータ（名前が入力されている行）だけ抽出し、インデックスを1から振り直す
    new_df = edited_df.dropna(subset=["名前"])
    new_df = new_df[new_df["名前"].str.strip() != ""]
    if "index" in new_df.columns:
        new_df = new_df.reset_index(drop=True)
    else:
        new_df = new_df.reset_index(drop=False)
    if "index" in new_df.columns:
        new_df["index"] = pd.Series(range(1, len(new_df) + 1), index=new_df.index)
    # print(new_df)
    # if len(new_df.index.dropna()) != len(new_df.index):
    #     new_df = new_df.reset_index(drop=False)
    st.session_state.df = new_df
    # 再描画を促すために、必要に応じて st.rerun() を使うこともありますが、
    # data_editor の場合はこの代入だけで次の操作時に反映されます。
    # 画面上のIndex表示を即座に更新したい場合は rerun を入れる
    st.rerun()

# num_per_team = st.number_input("1チームの人数", min_value=2, step=1, value=3)
num_per_team = st.number_input("チーム人数を入力してください（デフォルト3名）", min_value=2, step=1, value=3)

# 2. 実行ボタン
if st.button("チームを編成する", type="primary"):
    # valid_df = edited_df.dropna(subset=["名前"])
    # valid_df = valid_df[valid_df["名前"].str.strip() != ""]
    # 計算に使用する最終的なクリーンデータ
    valid_df = st.session_state.df.copy()

    if len(valid_df) < 4:
        st.error(f"4名以上で入力してください。（現在{len(valid_df)}名）。")
    else:
        result, error = solve_multi_team_division(valid_df, num_per_team)
        
        if result:
            teams, avgs = result
            # 選外
            all_selected = [m for team in teams for m in team]
            bench = [m for m in valid_df["名前"] if m not in all_selected]
            if bench:
                st.success(f"チーム編成完了！ ※全{len(valid_df)}人/1チーム{num_per_team}人なので、{len(teams)}チーム作り、{len(bench)}名余りました。")
            else:
                st.success(f"チーム編成完了！ ※全{len(valid_df)}人/1チーム{num_per_team}人なので、{len(teams)}チーム作りました。")

            # 結果表示
            cols = st.columns(len(teams))
            for i, (team, avg, col) in enumerate(zip(teams, avgs, cols)):
                with col:
                    st.write(f"**チーム {i+1}**")
                    st.caption(f"平均: {avg:.1f}cm")
                    for member in team:
                        h = valid_df.loc[valid_df["名前"] == member, "身長"].values[0]
                        st.write(f"・{member} ({h:.0f}cm)")
            
            # ★ 履歴に保存（今回のペアを記録）
            for team in teams:
                for pair in itertools.combinations(sorted(team), 2):
                    st.session_state.pair_history[pair] = st.session_state.pair_history.get(pair, 0) + 1
            
            if bench:
                st.info(f"今回の商余りメンバー: {', '.join(bench)}   ※適宜チーム編成してください。")

# 3. 使い方ヘルプ
with st.expander("使い方ヘルプ"):
    st.write("""
    - **行の追加**: テーブルの下部にある『＋』をクリックします。
    - **行の削除**: 行の左側を選択して `Del` キーを押します。
    - **チーム人数の入力**: チーム人数を入力することで、チーム数が変更されます。
    - **最適化**: 平均身長が同じになるように、ランダムでメンバー選定しています。余ったメンバーは適宜チームに入れてください。
    """)
    # st.write(
    # f"行の追加: テーブルの下部にある『＋』をクリックします。\n行の削除: 行の左側を選択して `Del` キーを押します。\n最適化: f\"{num_per_team}\"名1組でチームを作ります。ランダムでメンバー選定しています。余ったメンバーは適宜チームに入れてください。"
    # )
