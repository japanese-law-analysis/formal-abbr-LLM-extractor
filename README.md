# formal-abbr-LLM-extractor

本リポジトリは、法令条文（`choise_rand.json`）から略称と正式名称のペアを抽出し、結果をJSON形式で出力・評価するためのプロジェクトです。  
各条文に対して LLM（Large Language Model）を呼び出し、抽出結果を評価して正答率を算出します。

---

## ディレクトリ構造

```
formal-abbr-LLM-extractor
├── extracted_results
│   └── …                      # 抽出結果のJSONファイルが保存されるディレクトリ
├── law_text
│   └── choise_rand.json         # 入力データ (法令条文) が格納される
├── src
│   ├── main.py                  # メインのスクリプト
│   └── prompt.py                # プロンプト生成用スクリプト
├── LICENSE
└── README.md                    # 本ファイル
```

- **`law_text/choise_rand.json`**  
  法令文を含むJSONファイル。`text` フィールドに条文、`list` フィールドに ground truth (略称と正式名称のペア) が格納されています。

- **`src/main.py`**  
  メインスクリプト。  
  LLM に問い合わせ、抽出したペアと ground truth を比較し、正答率を算出します。  
  実行時にモデル名や Few-shot の種類などを指定できます。

- **`src/prompt.py`**  
  Few-shot プロンプトのサンプル文などを含むプロンプト生成用のモジュール。

---

## セットアップ

1. **Python 環境**
    - Python 3.7 以上推奨

2. **ライブラリのインストール**
    ```
    pip install openai tqdm
    ```

3. **OpenAI API キーの設定**
    - 環境変数 `OPENAI_API_KEY` を設定してください。
    - 例: Linux/Mac の場合は下記のようにターミナルで設定

      export OPENAI_API_KEY="sk-xxxxxxxxxxxxxx"

    - Windows の場合は PowerShell 等で同様の設定を行ってください。

---

## 使い方

1. **リポジトリをクローンまたはダウンロード**
    ```
    git clone git@github.com:japanese-law-analysis/formal-abbr-LLM-extractor.git
    ```

2. **ディレクトリ構成を整える**

- 上記のように `extracted_results/` と `law_text/`、`src/` が同階層にあることを確認してください。
- `law_text/choise_rand.json` に処理対象のデータを配置してください。

3. **スクリプトを実行**

- `src` ディレクトリへ移動して以下を実行します。

  cd src
  python main.py -m o1-mini -f none

- オプション:
    - `-m, --model`: 使用するモデル名 (例: `o1-mini`, `gpt-4o-mini`)
    - `-f, --few_shot`: Few-shot の種類 (`our`, `nakamura`, `none`)

4. **出力**

- 抽出結果として JSON ファイルが

  extracted_results/extracted_results_{MODEL_NAME}_{SAVE_PATH_POSTFIX}.json

  に都度保存されます。
- スクリプト実行完了時に、ground truth との比較による**正答率**をコンソールに表示します。

---

## 主なファイルの説明

### `src/main.py`

- **概要**  
  法令条文（`choise_rand.json`）から抜き出した `text` を LLM に投げ、抽出された略称・正式名称ペアを `extracted_results/` に JSON
  形式で保存します（途中で処理が中断しても、保存された分は再利用可能）。  
  また、抽出結果と ground truth (`list` フィールド) を比較し、正答率を算出します。

- **実行例**  
  cd src  
  python main.py -m o1-mini -f our

例では `o1-mini` というモデル名と、Few-shot を `our` タイプに設定して実行します。

### `src/prompt.py`

- **概要**  
  Few-shot のサンプルを含むプロンプト文字列を生成するモジュールです。  
  `few_shot_type` を切り替えることで使用するサンプルの数や内容を変更できます。

---

## 注意点

- OpenAI API の利用には無料クレジットや月額クレジットの上限があり、使いすぎると `insufficient_quota` などのエラーが出る場合があります。
- 大量データを一度に処理する場合はレートリミットに注意し、適宜分割実行やスリープを挟んでください。
- LLM の返すテキストをそのまま `json.loads()` するとエラーになることがあるため、`raw_content.replace("```json", "")`
  や `raw_content.replace("```", "")` のように不要なバッククォートを除去する対策をとっています。

---

- (c) Daiki Nishiyama / 西山 大輝
- GitHub: [Daiki Nishiyama](https://github.com/pfunami)
- [MIT License](./LICENSE)