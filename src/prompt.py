def get_user_prompt(law_text: str, few_shot_type: str):
    if few_shot_type == 'none':
        few_shot_text = ''
    else:
        few_shot_text = f"""
【サンプル1】
入力:
---
「〇〇」とは、△△をいう。
---
期待する出力:
[
  {{
    "formal": "△△",
    "abbr": "〇〇"
  }}
]

【サンプル2】
入力:
---
△△（以下「〇〇」という。）
---
期待する出力:
[
  {{
    "formal": "△△",
    "abbr": "〇〇"
  }}
]


【サンプル3】
入力:
---
〇〇（△△をいう。以下同じ。）
---
期待する出力:
[
  {{
    "formal": "△△",
    "abbr": "〇〇"
  }}
]
        """
        if 'our' in few_shot_type:
            few_shot_text = few_shot_text + """
【サンプル4】
入力:
---
〇〇（△△に規定する〇〇をいう。以下同じ。）
---
期待する出力:
[
  {{
    "formal": "△△に規定する〇〇",
    "abbr": "〇〇"
  }}
]
            """

    user_content = f"""
以下のタスクを行ってください。

【タスク】
- 入力として与えられるテキストには、法令文独特の形で「正式名称」と「略称」が定義されている可能性があります。
- これをすべて検出し、それぞれのペアを JSON 配列で出力してください。
- 略称が複数ある場合はすべて挙げること。
- 見つからなかった場合は空の配列 `[]` を返してください。
- 出力は JSON のみで、他の説明文は一切不要です。

【JSONの形式】
下記のような配列で返してください。配列要素が複数になる場合はカンマで区切ります。

[
  {{
    "formal": "正式名称",
    "abbr": "略称"
  }},
  {{
    "formal": "正式名称",
    "abbr": "略称"
  }}
]

{few_shot_text}

【本番入力】
---
{law_text}
---

**注意**:
- 略称と正式名称が見つかっても、その他の要素（定義されていない言葉や補足情報）は出力しないでください。
- 出力は valid な JSON 配列のみで、前後に余計な文章を書かないでください。
    """

    return user_content


if __name__ == '__main__':
    law_text = 'hogehogehogehogehogehogehogehogehogehogehogehogehogehogehogehoge'
    SAVE_PATH_POSTFIX = 'our'
    user_content = get_user_prompt(law_text, SAVE_PATH_POSTFIX)
    print(user_content)
