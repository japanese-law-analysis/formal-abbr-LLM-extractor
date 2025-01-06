import os
import json
import argparse
from openai import OpenAI
from tqdm import tqdm
from prompt import get_user_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_formal_abbr_from_law_text(law_text: str) -> list or None:
    """
    与えられた法令条文 law_text に対し、
    LLM へプロンプトを投げて「正式名称(formal)」「略称(abbr)」のペアを抽出させる。
    成功時は [{"formal":..., "abbr":...}, ...] のリストを返す。
    見つからなかった場合やエラー時は空リスト[]を返す。
    """

    # システムメッセージ (任意)
    system_content = (
        "あなたは日本語の法令文を解析し、略称と正式名称のペアを抽出するエキスパートです。"
        "出力はJSON形式のみで返してください。"
    )

    # ユーザーメッセージ (プロンプト)
    user_content = get_user_prompt(law_text=law_text, few_shot_type=FEW_SHOT_TYPE)

    try:
        if 'o1' in MODEL_NAME:
            # role: system 未対応
            message = [
                {"role": "user", "content": system_content + "\n" + user_content}
            ]
        else:
            message = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
        response = client.chat.completions.create(
            model=MODEL_NAME,
            # temperature=0.0,
            messages=message,
        )
        # 疎通確認用（リクエストID）
        # print("Request ID:", response._request_id)

        raw_content = response.choices[0].message.content.strip()
        raw_content = raw_content.replace("```json", "")
        raw_content = raw_content.replace("```", "")

        # JSONのパースを試みる
        result = json.loads(raw_content)

        # "formal" と "abbr" を持つオブジェクトの配列かどうかの簡単なバリデーション
        if isinstance(result, list):
            for elem in result:
                if not isinstance(elem, dict):
                    return []
                if "formal" not in elem or "abbr" not in elem:
                    return []
            return result
        else:
            return []
    except Exception as e:
        print("Error during LLM call or JSON parsing:", e)
        return None


def main():
    # 入力ファイルと出力ファイル名
    input_file = "../law_text/choise_rand.json"
    output_file = f"../extracted_results/extracted_results_{MODEL_NAME}_{SAVE_PATH_POSTFIX}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 元のデータを読み込み
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 既存の結果があれば読み込み（途中から再開したい場合など）
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []

    # 正答率計算用カウンタ
    num_abbr_gt = 0  # ground truth の 略称の総数
    num_abbr_correct = 0  # 正しく抽出された略称の数
    num_formal_correct = 0  # 略称が正しく抽出された中で、正式名称も合っていた数

    processed_idx = set([r["idx"] for r in results])

    for idx, item in enumerate(tqdm(data, desc="Processing", total=len(data))):
        text_content = item.get("text", "")
        file_name = item.get("file", "")
        gt_pairs = item.get("list", [])  # ground truth: [{ "formal":..., "abbr":...}, ...]

        if proc_idx := f'{file_name}_{idx}' in processed_idx:
            print(f"Skip: {proc_idx}")
            extracted_pairs = results[idx].get("extracted_pairs", [])
            print(f"Extracted: {extracted_pairs}")
        else:
            # LLM に問い合わせをして、抽出結果を得る
            extracted_pairs = extract_formal_abbr_from_law_text(text_content)
            if extracted_pairs is not None:
                # 結果を一つ追加
                results.append({
                    # idxはfile_nameとidxの組み合わせにする
                    "idx": f'{file_name}_{idx}',
                    "file": file_name,
                    "text": text_content,
                    "extracted_pairs": extracted_pairs
                })
                processed_idx.add(f'{file_name}_{idx}')

                # JSON ファイルにその都度保存（部分的にでも結果を残すため）
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                # 途中経過をコンソールに表示
                print(f"[{idx + 1}/{len(data)}] file={file_name} => extracted {len(extracted_pairs)} pairs (saved)")
            else:
                print(f"[{idx + 1}/{len(data)}] file={file_name} => extraction failed (skipped)")
                continue

        # --- 正答率のカウントを行う（最終的には全体での合計を出す）---
        for gt_pair in gt_pairs:
            gt_abbr = gt_pair.get("abbr", "")
            gt_formal = gt_pair.get("formal", "")
            if not gt_abbr:
                continue  # 略称が空ならスキップ

            num_abbr_gt += 1

            # LLM が抽出した中に同じ "abbr" があれば「略称正解」とみなす
            matched_extracted = None
            for epair in extracted_pairs:
                if epair["abbr"] == gt_abbr:
                    matched_extracted = epair
                    break

            if matched_extracted is not None:
                num_abbr_correct += 1
                # 更に正式名称が一致しているか確認
                if matched_extracted["formal"] == gt_formal:
                    num_formal_correct += 1

    print(f"\nDone! (Partial results are saved in {output_file})")

    # --- 最終的な正答率の計算 ---
    if num_abbr_gt == 0:
        print("【警告】ground truth の略称が1つもありません。正答率は算出できません。")
        return

    abbr_accuracy = num_abbr_correct / num_abbr_gt
    if num_abbr_correct == 0:
        formal_accuracy = 0.0
    else:
        formal_accuracy = num_formal_correct / num_abbr_correct

    print("\n----- 正答率 (最終集計) -----")
    print(f"略称を正しく抽出できている割合: {abbr_accuracy:.3f} "
          f"({num_abbr_correct}/{num_abbr_gt})")
    print(f"略称が正しく抽出された中で正式名称が合っている割合: {formal_accuracy:.3f} "
          f"({num_formal_correct}/{num_abbr_correct if num_abbr_correct > 0 else 1})")


if __name__ == "__main__":
    # argparse で model_name と few_show_type を受け取る
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", type=str, required=True, help="model name", choices=["o1-mini", "gpt-4o-mini"])
    parser.add_argument("-f", "--few_shot", type=str, required=True, help="few shot type",
                        choices=["our", "nakamura", "none"])
    args = parser.parse_args()
    MODEL_NAME = args.model
    FEW_SHOT_TYPE = args.few_shot
    SAVE_PATH_POSTFIX = FEW_SHOT_TYPE

    print(f'Model: {MODEL_NAME}, Few-shot type: {FEW_SHOT_TYPE}')
    main()
