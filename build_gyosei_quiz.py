"""
taki_questions_raw.json と kijutsu_questions_raw.json から
gyosei_quiz.html を生成する
"""

import json
import re

# データ読み込み
with open('taki_questions_raw.json', encoding='utf-8') as f:
    taki_raw = json.load(f)
with open('kijutsu_questions_raw.json', encoding='utf-8') as f:
    kijutsu_raw = json.load(f)


def fix_subject_from_title(title):
    if '憲法' in title:
        return '憲法'
    if '民法' in title:
        return '民法'
    if '行政法' in title or '行政事件' in title or '行手' in title or '行不服' in title:
        return '行政法'
    return '行政法'


def clean_question_text(text):
    """問題文から不要な行を除去してクリーンアップ"""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        # タイトル行（年度番号）は除去
        if re.match(r'^(令和|平成)\d+年・\d+｜', line):
            continue
        # 「次の文章...選びなさい」の指示文も除去
        if re.match(r'^次の文章', line) and '選びなさい' in line:
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()


def question_text_to_html(text, blanks):
    """問題文の空欄マーカーをHTMLのspanに変換。
    正解テキストの文字数に合わせて幅を事前確保することでレイアウトずれを防ぐ。
    """
    answer_map = {b['label']: b['answer'] for b in blanks}

    # 本文の & を先にエスケープ（空欄マーカーには & が無い）
    text = text.replace('&', '&amp;')

    def replace_blank(m):
        label = m.group(1)
        answer = answer_map.get(label, '')
        # 本物の答えを透明(visibility:hidden)で埋め込み、幅と改行を確定させる。
        # 選択時は色を出すだけなので一切レイアウトがずれない。
        ans_esc = (answer.replace('&', '&amp;')
                         .replace('<', '&lt;').replace('>', '&gt;'))
        return (f'<span class="blank" data-label="{label}">'
                f'<span class="bl-ans">{ans_esc}</span>'
                f'<span class="bl-lab">{label}</span></span>')

    result = re.sub(r'[\[［][\s　]*([アイウエ])[\s　]*[\]）］]', replace_blank, text)
    result = result.replace('\n', '<br>')
    return result


# データ整形
taki_data = []
for q in taki_raw:
    subject = fix_subject_from_title(q.get('title', '')) or q.get('subject', '行政法')
    clean_text = clean_question_text(q['question_text'])
    q_html = question_text_to_html(clean_text, q['blanks'])
    taki_data.append({
        'source': q['source'],
        'year': q['year'],
        'seireki': q['seireki'],
        'qnum': q['qnum'],
        'subject': subject,
        'title': q.get('title', ''),
        'questionHtml': q_html,
        'blanks': q['blanks'],
        'choices': q['choices'],
    })

kijutsu_data = []
for k in kijutsu_raw:
    subject = fix_subject_from_title(k.get('title', '')) or k.get('subject', '行政法')
    # 問題文の先頭にあるタイトル行を除去
    problem = k['problem_text']
    lines = problem.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^(令和|平成)\d+年・\d+｜', line):
            continue
        cleaned_lines.append(line)
    problem_clean = '\n'.join(cleaned_lines).strip()

    kijutsu_data.append({
        'source': k['source'],
        'year': k['year'],
        'seireki': k['seireki'],
        'qnum': k['qnum'],
        'subject': subject,
        'title': k.get('title', ''),
        'problemText': problem_clean[:1500],
        'modelAnswer': k.get('model_answer', ''),
    })


taki_json = json.dumps(taki_data, ensure_ascii=False)
kijutsu_json = json.dumps(kijutsu_data, ensure_ascii=False)

HTML = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>行政書士 多肢選択・記述式 過去問</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', sans-serif;
  background: #f5f4f0;
  color: #1a1a1a;
  min-height: 100vh;
  padding: 12px;
}}

.container {{
  max-width: 640px;
  margin: 0 auto;
}}

/* タブ */
.tabs {{
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}}

.tab-btn {{
  flex: 1;
  padding: 10px 4px;
  border: 2px solid #1a1a2e;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  background: #fff;
  color: #1a1a2e;
  transition: all 0.15s;
}}

.tab-btn.active {{
  background: #1a1a2e;
  color: #fff;
}}

/* フィルタ */
.filter-row {{
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
}}

.filter-select {{
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: inherit;
  font-size: 13px;
  background: #fff;
  color: #222;
}}

.btn-random {{
  padding: 8px 14px;
  background: #1a1a2e;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  white-space: nowrap;
}}

/* ヘッダ */
header {{
  text-align: center;
  padding: 12px 0 10px;
}}

header .tag {{
  display: inline-block;
  background: #1a1a2e;
  color: #fff;
  font-size: 11px;
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 6px;
}}

header h1 {{
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.4;
}}

header .sub {{
  font-size: 11px;
  color: #888;
  margin-top: 3px;
}}

/* ナビ */
.nav-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}}

.nav-btn {{
  padding: 8px 14px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  background: #fff;
  color: #333;
}}

.nav-btn:hover {{ background: #f0f0f0; }}

.nav-count {{
  flex: 1;
  text-align: center;
  font-size: 12px;
  color: #888;
}}

/* プログレス */
.progress-wrap {{
  margin-bottom: 12px;
}}

.progress-bar-bg {{
  background: #ddd;
  border-radius: 4px;
  height: 4px;
  overflow: hidden;
}}

.progress-bar-fill {{
  background: #1a1a2e;
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}}

.progress-text {{
  font-size: 11px;
  color: #888;
  margin-top: 4px;
  text-align: right;
}}

/* カード */
.card {{
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  margin-bottom: 12px;
  border: 1px solid #e8e6e0;
}}

.card-label {{
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #888;
  margin-bottom: 10px;
  text-transform: uppercase;
}}

.q-text {{
  font-size: 13px;
  line-height: 2.0;
  color: #222;
}}

.blank {{
  position: relative;
  display: inline-block;
  vertical-align: middle;
  white-space: nowrap;
  text-align: center;
  padding: 1px 6px;
  margin: 0 1px;
  border: 1.5px solid #bbb;
  border-radius: 5px;
  background: #f4f4f6;
  font-weight: 700;
  transition: border-color 0.15s, background 0.15s;
}}

/* 本物の答え（透明で場所を確保。選択時に色を出すだけ） */
.blank .bl-ans {{
  visibility: hidden;
  color: #1a1a2e;
}}

/* 空欄ラベル（ア/イ/ウ/エ）を確保した幅の中央に重ねて表示 */
.blank .bl-lab {{
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
}}

.blank.active {{ border-color: #1a1a2e; background: #e9e9f2; }}
.blank.active .bl-lab {{ color: #1a1a2e; }}

.blank.answered .bl-ans {{ visibility: visible; }}
.blank.answered .bl-lab {{ display: none; }}

.blank.correct {{ border-color: #2a9d5c; background: #e6f4ec; }}
.blank.correct .bl-ans {{ color: #1e7a44; }}

.blank.wrong {{ border-color: #e05252; background: #fbeaea; }}
.blank.wrong .bl-ans {{ color: #b93333; }}

/* 解答パネル */
.answer-panel {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}}

.answer-item {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}}

.answer-item .a-label {{
  font-weight: 700;
  color: #888;
  min-width: 1em;
}}

.answer-item .a-text {{
  background: #f5f4f0;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 12px;
  color: #555;
  min-width: 4em;
  text-align: center;
}}

.answer-item .a-text.correct {{
  background: #e6f4ec;
  border-color: #2a9d5c;
  color: #1e7a44;
}}

.answer-item .a-text.wrong {{
  background: #fdecea;
  border-color: #e05252;
  color: #b93333;
}}

/* 選択肢エリア */
.select-area {{
  background: #fff;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid #e8e6e0;
  margin-bottom: 12px;
}}

.select-label {{
  font-size: 11px;
  color: #888;
  margin-bottom: 4px;
}}

.current-q {{
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 12px;
}}

.choices {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}}

.choice-btn {{
  background: #f5f4f0;
  border: 1px solid #e0ddd6;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  color: #222;
  cursor: pointer;
  text-align: center;
  font-family: inherit;
  line-height: 1.4;
  transition: all 0.15s;
}}

.choice-btn:hover {{ background: #eeedf8; border-color: #1a1a2e; }}

.choice-btn.used {{
  opacity: 0.3;
  pointer-events: none;
}}

/* 結果 */
.result-card {{
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid #e8e6e0;
  text-align: center;
  margin-bottom: 12px;
}}

.result-score {{
  font-size: 44px;
  font-weight: 800;
  color: #1a1a2e;
  line-height: 1;
  margin-bottom: 4px;
}}

.result-score span {{
  font-size: 18px;
  font-weight: 400;
  color: #888;
}}

.result-label {{
  font-size: 13px;
  color: #555;
  margin-bottom: 16px;
}}

.result-detail {{
  text-align: left;
  border-top: 1px solid #eee;
  padding-top: 14px;
  margin-bottom: 16px;
}}

.result-row {{
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}}

.result-row:last-child {{ border-bottom: none; }}

.rr-icon {{ font-size: 14px; min-width: 16px; }}
.rr-label {{ font-weight: 700; min-width: 16px; color: #1a1a2e; }}
.rr-answer {{ flex: 1; }}
.rr-your {{ color: #e05252; font-size: 11px; margin-top: 2px; }}

.btn-next-q {{
  width: 100%;
  background: #1a1a2e;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 13px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  margin-top: 8px;
}}

/* 記述式 */
.kijutsu-problem {{
  font-size: 13px;
  line-height: 2.0;
  color: #222;
  white-space: pre-wrap;
}}

.btn-reveal {{
  width: 100%;
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 12px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  margin-top: 4px;
  transition: background 0.2s;
}}

.btn-reveal:hover {{ background: #e0e0e0; }}

.answer-box {{
  background: #1a1a2e;
  color: #e8e6ff;
  border-radius: 12px;
  padding: 16px;
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.9;
}}

.answer-box h3 {{
  font-size: 12px;
  letter-spacing: 0.1em;
  color: #aaa;
  margin-bottom: 8px;
}}

.answer-text {{
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  line-height: 1.8;
}}

.hidden {{ display: none; }}
</style>
</head>
<body>
<div class="container">

  <!-- タブ -->
  <div class="tabs">
    <button class="tab-btn active" onclick="switchMode('taki')">多肢選択式</button>
    <button class="tab-btn" onclick="switchMode('kijutsu')">記述式</button>
  </div>

  <!-- フィルタ -->
  <div class="filter-row">
    <select class="filter-select" id="yearFilter" onchange="applyFilter()">
      <option value="">全年度</option>
    </select>
    <button class="btn-random" onclick="goRandom()">ランダム</button>
  </div>

  <!-- ナビ -->
  <div class="nav-row">
    <button class="nav-btn" onclick="goPrev()">&lt; 前</button>
    <span class="nav-count" id="navCount">-</span>
    <button class="nav-btn" onclick="goNext()">次 &gt;</button>
  </div>

  <!-- ======== 多肢選択式 ======== -->
  <div id="takiSection">

    <header>
      <div class="tag" id="takiTag">-</div>
      <h1 id="takiTitle">-</h1>
    </header>

    <div class="progress-wrap">
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" id="progressBar"></div>
      </div>
      <div class="progress-text" id="progressText">0 / 4</div>
    </div>

    <div class="card">
      <div class="card-label">問題文</div>
      <div class="q-text" id="qText"></div>
    </div>

    <div class="select-area" id="selectArea">
      <div class="current-q" id="curLabel">-</div>
      <div class="choices" id="choices"></div>
    </div>

    <div class="result-card hidden" id="resultCard"></div>

  </div>

  <!-- ======== 記述式 ======== -->
  <div id="kijutsuSection" class="hidden">

    <header>
      <div class="tag" id="kijutsuTag">-</div>
      <h1 id="kijutsuTitle">記述式</h1>
    </header>

    <div class="card">
      <div class="card-label">問題</div>
      <div class="kijutsu-problem" id="kijutsuProblem"></div>
    </div>

    <button class="btn-reveal" id="revealBtn" onclick="revealAnswer()">模範解答を見る</button>

    <div class="answer-box hidden" id="answerBox">
      <h3>模範解答</h3>
      <div class="answer-text" id="answerText"></div>
    </div>

  </div>

</div>

<script>
const TAKI = {taki_json};
const KIJUTSU = {kijutsu_json};

let mode = 'taki';          // 'taki' | 'kijutsu'
let filteredTaki = [...TAKI];
let filteredKijutsu = [...KIJUTSU];
let takiIdx = 0;
let kijutsuIdx = 0;

// blank state
let current = 0;
let answers = [];
let shuffledChoices = [];

// 年度リストを生成
function buildYearOptions() {{
  const years = [...new Set(TAKI.map(q => q.year))];
  const sel = document.getElementById('yearFilter');
  years.forEach(y => {{
    const opt = document.createElement('option');
    opt.value = y;
    opt.textContent = y;
    sel.appendChild(opt);
  }});
}}

function switchMode(m) {{
  mode = m;
  document.querySelectorAll('.tab-btn').forEach((b,i) => {{
    b.classList.toggle('active', (i === 0 && m === 'taki') || (i === 1 && m === 'kijutsu'));
  }});
  document.getElementById('takiSection').classList.toggle('hidden', m !== 'taki');
  document.getElementById('kijutsuSection').classList.toggle('hidden', m !== 'kijutsu');
  updateNavCount();
  if (m === 'taki') loadTaki(takiIdx);
  else loadKijutsu(kijutsuIdx);
}}

function applyFilter() {{
  const year = document.getElementById('yearFilter').value;
  if (year) {{
    filteredTaki = TAKI.filter(q => q.year === year);
    filteredKijutsu = KIJUTSU.filter(k => k.year === year);
  }} else {{
    filteredTaki = [...TAKI];
    filteredKijutsu = [...KIJUTSU];
  }}
  takiIdx = 0;
  kijutsuIdx = 0;
  if (mode === 'taki') loadTaki(0);
  else loadKijutsu(0);
}}

function goRandom() {{
  if (mode === 'taki') {{
    takiIdx = Math.floor(Math.random() * filteredTaki.length);
    loadTaki(takiIdx);
  }} else {{
    kijutsuIdx = Math.floor(Math.random() * filteredKijutsu.length);
    loadKijutsu(kijutsuIdx);
  }}
}}

function goPrev() {{
  if (mode === 'taki') {{
    takiIdx = (takiIdx - 1 + filteredTaki.length) % filteredTaki.length;
    loadTaki(takiIdx);
  }} else {{
    kijutsuIdx = (kijutsuIdx - 1 + filteredKijutsu.length) % filteredKijutsu.length;
    loadKijutsu(kijutsuIdx);
  }}
}}

function goNext() {{
  if (mode === 'taki') {{
    takiIdx = (takiIdx + 1) % filteredTaki.length;
    loadTaki(takiIdx);
  }} else {{
    kijutsuIdx = (kijutsuIdx + 1) % filteredKijutsu.length;
    loadKijutsu(kijutsuIdx);
  }}
}}

function updateNavCount() {{
  const total = mode === 'taki' ? filteredTaki.length : filteredKijutsu.length;
  const idx = mode === 'taki' ? takiIdx : kijutsuIdx;
  document.getElementById('navCount').textContent = (idx + 1) + ' / ' + total;
}}

// ======== 多肢選択式 ========
function loadTaki(idx) {{
  takiIdx = idx;
  updateNavCount();
  const q = filteredTaki[idx];
  if (!q) return;

  document.getElementById('takiTag').textContent = q.source;
  document.getElementById('takiTitle').textContent = '多肢選択式 ' + q.subject;

  current = 0;
  answers = q.blanks.map(() => null);
  shuffledChoices = shuffle([...q.choices]);

  document.getElementById('qText').innerHTML = q.questionHtml;
  document.getElementById('selectArea').classList.remove('hidden');
  document.getElementById('resultCard').classList.add('hidden');

  updateProgress(q);
  updateActiveBlank(q);
  renderChoices(q);
}}

function shuffle(arr) {{
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }}
  return a;
}}

function updateProgress(q) {{
  const done = answers.filter(a => a !== null).length;
  const total = q.blanks.length;
  const pct = (done / total) * 100;
  document.getElementById('progressBar').style.width = pct + '%';
  document.getElementById('progressText').textContent = done + ' / ' + total;
}}

function updateActiveBlank(q) {{
  q.blanks.forEach((b, i) => {{
    document.querySelectorAll('[data-label="' + b.label + '"]').forEach(el => {{
      el.classList.remove('active');
      if (answers[i] === null && i === current) el.classList.add('active');
    }});
  }});
  if (current < q.blanks.length) {{
    document.getElementById('curLabel').textContent = q.blanks[current].label + ' を選んでください';
  }}
}}

function renderChoices(q) {{
  const grid = document.getElementById('choices');
  grid.innerHTML = '';
  const usedTexts = answers.filter(a => a !== null);
  shuffledChoices.forEach(c => {{
    const btn = document.createElement('button');
    btn.className = 'choice-btn' + (usedTexts.includes(c.text) ? ' used' : '');
    btn.textContent = c.text;
    btn.onclick = () => selectAnswer(c.text, q);
    grid.appendChild(btn);
  }});
}}

function selectAnswer(choiceText, q) {{
  if (current >= q.blanks.length) return;
  answers[current] = choiceText;

  const b = q.blanks[current];
  const isCorrect = choiceText === b.answer;

  // 透明で入れてある正解を表示し、正誤で色を変える（幅は確定済みなのでずれない）
  document.querySelectorAll('[data-label="' + b.label + '"]').forEach(el => {{
    el.classList.remove('active');
    el.classList.add('answered', isCorrect ? 'correct' : 'wrong');
  }});

  current++;
  updateProgress(q);

  if (current >= q.blanks.length) {{
    showTakiResult(q);
  }} else {{
    updateActiveBlank(q);
    renderChoices(q);
  }}
}}

function showTakiResult(q) {{
  document.getElementById('selectArea').classList.add('hidden');

  const score = answers.filter((a, i) => a === q.blanks[i].answer).length;
  const msgs = ['もう一度！', 'あと少し！', 'いい感じ！', 'ほぼ完璧！', '満点！'];
  const rc = document.getElementById('resultCard');
  rc.classList.remove('hidden');

  let html = `<div class="result-score">${{score}}<span> / ${{q.blanks.length}}</span></div>
    <div class="result-label">${{msgs[score] || ''}}</div>
    <div class="result-detail">`;

  q.blanks.forEach((b, i) => {{
    const ok = answers[i] === b.answer;
    html += `<div class="result-row">
      <span class="rr-icon">${{ok ? 'O' : 'X'}}</span>
      <span class="rr-label">${{b.label}}</span>
      <div class="rr-answer">${{b.answer}}${{!ok ? `<div class="rr-your">あなた：${{answers[i]}}</div>` : ''}}</div>
    </div>`;
  }});

  html += `</div>
    <button class="btn-next-q" onclick="goNext()">次の問題へ</button>`;

  rc.innerHTML = html;
}}

// ======== 記述式 ========
function loadKijutsu(idx) {{
  kijutsuIdx = idx;
  updateNavCount();
  const k = filteredKijutsu[idx];
  if (!k) return;

  document.getElementById('kijutsuTag').textContent = k.source;
  document.getElementById('kijutsuTitle').textContent = '記述式 ' + k.subject;
  document.getElementById('kijutsuProblem').textContent = k.problemText;
  document.getElementById('revealBtn').classList.remove('hidden');
  document.getElementById('answerBox').classList.add('hidden');
  document.getElementById('answerText').textContent = k.modelAnswer || '（解答データなし）';
}}

function revealAnswer() {{
  document.getElementById('revealBtn').classList.add('hidden');
  document.getElementById('answerBox').classList.remove('hidden');
}}

// 初期化
buildYearOptions();
applyFilter();
</script>
</body>
</html>'''

with open('gyosei_quiz.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print('gyosei_quiz.html を生成しました')
print(f'多肢選択式: {len(taki_data)}問')
print(f'記述式: {len(kijutsu_data)}問')
