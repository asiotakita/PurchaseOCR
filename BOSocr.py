import os
import re
import json
import pandas as pd
import google.generativeai as genai
from pdf2image import convert_from_path
import sys
import time

# --- 設定 ---
API_KEY = "AIzaSyCBNDpDkQOdYaVV4p_XYg_ik117KY_jTSc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# 帳票ごとの定義
REPORT_CONFIGS = {
    "伸栄伝導機工の請求書": {
        "prompt": """
        あなたは伸栄伝導機工のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["右上頁"."日付", "区分", "伝票No", "メーカー名／商品コード", "商品名", "単位", "数量", "単価", "金額", "ご注文番号", "備考"]
        """
    },
    "藤本産業の請求書": {
        "prompt": """
        あなたは藤本産業のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["取引日付", "伝票番号・行", "材質", "表面処理", "商品名", "寸法", "備考", "数量", "単価", "金額", "先方注文No.", "Page"]
        """
    },
    "サンワメタルス": {
        "prompt": """
        あなたはサンワメタルスのデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["発送日", "受注番号", "貴社注番", "材質", "寸法", "F仕様", "単価", "合計"]
        """
    },
    "ミスミの請求書": {
        "prompt": """
        あなたはミスミの請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["形上年月日", "納品書番号", "注文番号・商品名称・型式", "数量", "単価", "御買上額"]
        """
    },
    "共立エーティエスの請求書": {
        "prompt": """
        あなたは共立エーティエスの請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["日付", "伝票番号", "摘要", "数量", "単価", "金額", "備考"]
        """
    },
    "高洋電機の請求書": {
        "prompt": """
        あなたは高洋電機の請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["ページ番号","納入日", "伝票No", "御注文番号", "商品名", "数量", "単価", "金額(税別)"]
        """
    },
    "三和精鋼の請求書": {
        "prompt": """
        あなたは三和精鋼の請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["計上日","依頼No.", "品名", "寸法", "単位", "数量", "単価", "金額"]
        """
    },
    "東機工の請求書": {
        "prompt": """
        あなたは東機工の請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["伝票日付","伝票番号", "区分", "商品コード商品名", "数量", "単価", "金額", "備考"]
        """
    },
    "ACSの請求書": {
        "prompt": """
        あなたはACSの請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["日付","売上No.", "発注No.", "品名／品番", "数量", "単価", "金額"]
        """
    },
    "白銅の請求書": {
        "prompt": """
        あなたは白銅の請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["計上日","品名", "寸法", "員数",  "単価", "税抜金額", "注番（返品摘要）"]
        """
    },
    "サステック東北の請求書": {
        "prompt": """
        あなたはサステック東北の請求書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["日付","商品名", "寸法", "員数", "単位", "重量","単価", "金額", "注番"]
        """
    },
    "UKの納品書": {
        "prompt": """
        あなたはUKの納品書のデータ抽出専門家です。以下の画像からデータを抽出し、JSONリストで回答してください。
        キー: ["売上日", "No.","品名", "数量", "単価", "金額", "備考", "QRコード"]
        """
    }
}

def append_to_excel(data, excel_path):
    df_new = pd.DataFrame(data)
    if os.path.exists(excel_path):
        df_existing = pd.read_excel(excel_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(excel_path, index=False)
    else:
        df_new.to_excel(excel_path, index=False)

def process_pdf_to_excel(pdf_path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    pages = convert_from_path(pdf_path, poppler_path=r'C:\poppler\Library\bin')
    
    for i, page in enumerate(pages):
        image_path = os.path.join(BASE_DIR, f"temp_page_{i}.png")
        page.save(image_path, "PNG")
        sample_file = genai.upload_file(path=image_path)
        
        # 帳票タイプの判定（より正確に）
        type_res = model.generate_content([
            "この画像は『藤本産業の納品書』『白銅の請求書』『サステック東北の請求書』『サンワメタルスの納品書』『伸栄伝導機工の請求書』『藤本産業の請求書』『ミスミの請求書』『共立エーティエスの請求書』『高洋電機の請求書』『三和精鋼の請求書』『ACSの請求書』『東機工の請求書』のどれですか？名称のみで回答してください。", 
            sample_file
        ])
        report_type = type_res.text.strip()
        print(f"判定結果: {report_type}")
        
        # 定義が存在するか確認
        if report_type in REPORT_CONFIGS:
            prompt = REPORT_CONFIGS[report_type]["prompt"]
            response = model.generate_content([prompt, sample_file])
            
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                append_to_excel(data, f"{report_type}_result.xlsx")
        else:
            print(f"未知の形式です: {report_type}")
        
        os.remove(image_path)
        genai.delete_file(sample_file.name)

if __name__ == "__main__":
    try:
        target = sys.argv[1] if len(sys.argv) > 1 else "input_document.pdf"
        process_pdf_to_excel(target)
    except Exception as e:
        print(f"エラー発生: {e}")
        sys.exit(1)
