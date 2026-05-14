import time
import os
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

INPUT_DIR = "input"
PROCESSED_DIR = "processed"

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".pdf"):
            return
        
        print(f"検知しました: {event.src_path}")
        
        # 1. OCR処理を実行し、結果（成功かどうか）を取得
        result = subprocess.run(["python", "Packinglistocr.py", event.src_path])
        
        if result.returncode == 0: # 正常終了した場合のみ移動
            # 日時を取得して新しいファイル名を作成
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            #new_filename = f"fujimot-{timestamp}.pdf"
            path = event.src_path
            # ファイル名だけを取得
            filename = os.path.basename(path)

            new_filename = f"{filename}-{timestamp}.pdf"
            dest_path = os.path.join(PROCESSED_DIR, new_filename)
            
            # ファイルを移動して名前を変更
            shutil.move(event.src_path, dest_path)
            print(f"処理成功: {new_filename} へ移動しました。")
        else:
            print("OCR処理でエラーが発生したため、移動は行いませんでした。")

if __name__ == "__main__":
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    observer = Observer()
    observer.schedule(PDFHandler(), INPUT_DIR, recursive=False)
    observer.start()
    
    print(f"監視開始: ./{INPUT_DIR} フォルダ...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    