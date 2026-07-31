import streamlit as st
import pandas as pd
import random
import statistics
import itertools  # ペア抽出用に追加

# --- カスタムCSS（既存のもの＋ボタンの縦幅調整） ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0px !important; }
    div.stButton > button { 
        width: 100%; 
        padding: 0.5rem 1rem; /* スマホで押しやすい高さ */
    }
    </style>
    """, unsafe_allow_html=True)

# --- ページ設定 ---
st.set_page_config(page_title="チーム編成アプリ", layout="wide")

# --- 履歴管理用のセッション状態 ---
if "pair_history" not in st.session_state:
    st.session_state.pair_history = {}

def solve_multi_team_division(member_df, num_per_team, iterations=10000):
    df_clean = member_df.reset_index(drop=True)
    members = dict(zip(df_clean["名前"], df_clean["身長"]))    
    member_names = list(members.keys())
    total_members = len(member_names)
    
    num_teams = total_members // num_per_team
    active_member_count = num_teams * num_per_team
    
    if num_teams < 2:
        return None, f"エラー: 2チーム以上作るには{num_per_team * 2}名以上の登録が必要です。"
    
    best_score = float('inf')
    best_assignment = None
    PENALTY_WEIGHT = 5.0 

    for _ in range(iterations):
        selected_members = random.sample(member_names, active_member_count)
        current_teams = []
        penalty = 0
        
        for i in range(num_teams):
            team = selected_members[i * num_per_team : (i + 1) * num_per_team]
            current_teams.append(team)
            
            for pair in itertools.combinations(sorted(team), 2):
                if pair in st.session_state.pair_history:
                    penalty += st.session_state.pair_history[pair] * PENALTY_WEIGHT

        averages = [sum(members[m] for m in team) / num_per_team for team in current_teams]
        height_score = statistics.stdev(averages)
        total_score = height_score + penalty
        
        if total_score < best_score:
            best_score = total_score
            best_assignment = (current_teams, averages)
            if total_score == 0: break

    return best_assignment, None

# --- UI部分 ---
st.markdown('<h4>🏃‍♂️ チーム編成アプリ（4名〜）</h4>', unsafe_allow_html=True)
# st.write("メンバーの名前と身長を入力してください（4名〜）。")

# サイドバー設定
with st.sidebar:
    st.header("設定")
    if st.button("対戦履歴をリセット"):
        st.session_state.pair_history = {}
        st.success("履歴をクリアしました。")
    st.write(f"現在の記録ペア数: {len(st.session_state.pair_history)}")

# 初期データの作成と保持
if "df" not in st.session_state:
    initial_data = [
            {"名前": "はるとくん", "身長": 175},
            {"名前": "さなちゃん", "身長": 167}, 
            {"名前": "ごう",       "身長": 165},
            {"名前": "りく",       "身長": 165}, 
            {"名前": "ゆうだい",   "身長": 165},
            {"名前": "ゆりりん",   "身長": 155}, 
            {"名前": "ゆうあ",     "身長": 155},
            {"名前": "おうすけ",   "身長": 155},
            {"名前": "しりゅう",   "身長": 155}, 
            {"名前": "あいな",     "身長": 140},
            {"名前": "わっくん",   "身長": 155}, 
            {"名前": "そうちゃん", "身長": 150},
            {"名前": "ゆきちゃん", "身長": 135}, 
            {"名前": "みきちゃん", "身長": 130},
            {"名前": "こっとん",   "身長": 140},
            {"名前": "かずきくん", "身長": 135},
            {"名前": "じゅんくん", "身長": 135},
            {"名前": "えみこちゃん", "身長": 130},
            {"名前": "みなこちゃん", "身長": 120},
            {"名前": "みゆちゃん",   "身長": 135},
            {"名前": "みよりちゃん", "身長": 135},
            {"名前": "そうちゃん（2年生）", "身長": 135},
        ]
    df = pd.DataFrame(initial_data)
    df.index = range(1, len(df) + 1)
    st.session_state.df = df

# =================================================================
# 📋 テーブルの変更を監視・維持するコールバック関数
# =================================================================
def on_table_change():
    changes = st.session_state.member_editor
    current_df = st.session_state.df.copy()

    # テーブル上で直接「行削除」が行われた場合
    if changes["deleted_rows"]:
        indices_to_drop = [current_df.index[i] for i in changes["deleted_rows"]]
        current_df = current_df.drop(indices_to_drop)

    # テーブル最下部の小さな「＋」で行追加された場合（念のため対応）
    if changes["added_rows"]:
        for row in changes["added_rows"]:
            name = row.get("名前", "")
            height = row.get("身長", 160)
            next_idx = current_df.index.max() + 1 if not current_df.empty else 1
            current_df.loc[next_idx] = [name, height]

    # 既存の行が直接編集された場合
    if changes["edited_rows"]:
        for row_idx, updated_cols in changes["edited_rows"].items():
            actual_idx = current_df.index[row_idx]
            for col_name, val in updated_cols.items():
                current_df.loc[actual_idx, col_name] = val

    # クリーンアップ（空欄除外とインデックスの1からの綺麗な振り直し）
    new_df = current_df.dropna(subset=["名前"])
    new_df = new_df[new_df["名前"].str.strip() != ""]
    new_df = new_df.reset_index(drop=True)
    new_df.index = range(1, len(new_df) + 1)
    
    st.session_state.df = new_df


# 1. 編集可能なテーブル
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    width=300,
    column_config={
        "名前": st.column_config.TextColumn("名前", required=True),
        "身長": st.column_config.NumberColumn("身長 (cm)", format="%.0f", min_value=100, max_value=200),
    },
    height=int((len(st.session_state.df) + 1) * 41),
    key="member_editor",
    on_change=on_table_change
)

# =================================================================
# ➕ メンバーをクイック追加（パターン①のUI）
# =================================================================
# st.markdown("##### ➕ メンバーをクイック追加")
st.write("メンバーの名前と身長を入力してください。")
c1, c2, c3 = st.columns([2, 2, 1.5])
with c1:
    new_name = st.text_input("名前", key="input_name", placeholder="例: たろう", label_visibility="collapsed")
with c2:
    new_height = st.number_input("身長", min_value=100, max_value=200, value=160, step=1, key="input_height", label_visibility="collapsed")
with c3:
    if st.button("追加する"):
        if new_name.strip():
            current_df = st.session_state.df.copy()
            # 末尾の次の連番を計算して安全に追加
            next_idx = current_df.index.max() + 1 if not current_df.empty else 1
            current_df.loc[next_idx] = [new_name.strip(), new_height]
            st.session_state.df = current_df
            st.rerun()  # 追加後に即時反映
        else:
            st.warning("名前を入力してください")


num_per_team = st.number_input("チーム人数を入力してください（デフォルト3名）", min_value=2, step=1, value=3)

# 2. 実行ボタン
if st.button("チームを編成する", type="primary"):
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
    - **行の追加**: 上部のクイック追加フォームに名前と身長を入力し「追加する」ボタンを押します。
    - **行の削除**: テーブルの行の左側を選択して `Del` キーを押します。
    - **チーム人数の入力**: チーム人数を入力することで、チーム数が変更されます。
    - **最適化**: 平均身長が同じになるように、ランダムでメンバー選定しています。余ったメンバーは適宜チームに入れてください。
    """)
