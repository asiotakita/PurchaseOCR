import google.generativeai as genai
import os

# あなたのAPIキーを入れてください
genai.configure(api_key="AIzaSyCBNDpDkQOdYaVV4p_XYg_ik117KY_jTSc")

# 利用可能なモデルをリストアップ
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"利用可能: {m.name}")
        