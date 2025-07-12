# 必要な標準ライブラリ・外部ライブラリをインポート
import os
import shutil
import subprocess
import qrcode
from pathlib import Path
from PIL.ImageQt import ImageQt
from PIL import Image
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QPushButton, QListWidget,
    QLabel, QFileDialog, QMessageBox, QInputDialog, QDialog, QSplitter
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

# メインの画面
class MainWindow(QWidget):
    def __init__(self, dictionary_dir):
        super().__init__()
        self.setWindowTitle("辞書ファイル管理ツール")

        # フォルダパスの設定など
        self.dictionary_dir = os.path.join(dictionary_dir, "base_dictionary")
        self.saved_dir = os.path.join(dictionary_dir, "saved_dictionary")
        self.onedrive_dir = os.path.expanduser("~/OneDrive/MyIMEBackup")

        os.makedirs(self.dictionary_dir, exist_ok=True)
        os.makedirs(self.saved_dir, exist_ok=True)
        os.makedirs(self.onedrive_dir, exist_ok=True)

        self.entries = []
        self.current_file = None

        self.init_ui()
        self.refresh_file_list()

    # 画面設計
    def init_ui(self):
        # 左側
        # ファイル操作パネル
        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.load_selected_file)

        # ファイル操作ボタン
        new_file_button = QPushButton("新規辞書ファイル作成")
        remove_file_button = QPushButton("辞書ファイル削除")
        open_folder_button = QPushButton("辞書フォルダを開く")

        new_file_button.clicked.connect(self.create_new_file)
        remove_file_button.clicked.connect(self.remove_selected_file)
        open_folder_button.clicked.connect(self.open_dictionary_folder)

        file_btns = QHBoxLayout()
        file_btns.addWidget(new_file_button)
        file_btns.addWidget(remove_file_button)

        # 単語入力フォーム
        self.yomi_input = QLineEdit()
        self.yomi_input.setMaxLength(60)

        self.hyouki_input = QLineEdit()
        self.hyouki_input.setMaxLength(60)

        # 品詞は選択
        self.hinshi_combo = QComboBox()
        self.hinshi_combo.addItems([
            "名詞", "動詞", "形容詞", "副詞", "連体詞", "接続詞", "感動詞", "記号", "カスタム名詞"
        ])

        # txtファイルに追加
        add_button = QPushButton("辞書に追加")
        add_button.clicked.connect(self.add_entry)

        # 入力フォーム
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("読み"))
        input_layout.addWidget(self.yomi_input)
        input_layout.addWidget(QLabel("表記"))
        input_layout.addWidget(self.hyouki_input)
        input_layout.addWidget(QLabel("品詞"))
        input_layout.addWidget(self.hinshi_combo)
        input_layout.addWidget(add_button)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("辞書ファイル一覧"))
        left_layout.addWidget(self.file_list)
        left_layout.addLayout(file_btns)
        left_layout.addWidget(open_folder_button)
        left_layout.addSpacing(20)
        left_layout.addLayout(input_layout)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(300)

        # 中央
        # 単語一覧テーブル
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["読み", "表記", "品詞"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(header.ResizeMode.Stretch)
        self.table.setMinimumWidth(400)

        # 単語の編集・削除
        edit_button = QPushButton("編集")
        delete_button = QPushButton("削除")
        edit_button.clicked.connect(self.edit_entry)
        delete_button.clicked.connect(self.delete_entry)

        table_btns = QHBoxLayout()
        table_btns.addWidget(edit_button)
        table_btns.addWidget(delete_button)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.table)
        center_layout.addLayout(table_btns)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # 右側
        # エクスポート・バックアップ
        export_google_button = QPushButton("Google日本語入力 / Mozc 用エクスポート")
        export_msime_button = QPushButton("Microsoft IME 用エクスポート")
        export_atok_button = QPushButton("ATOK 用エクスポート")
        export_skk_button = QPushButton("SKK 用エクスポート")
        backup_onedrive_btn = QPushButton("OneDriveにバックアップ")
        restore_onedrive_btn = QPushButton("OneDriveから復元")

        export_google_button.clicked.connect(self.export_google_mozc)
        export_msime_button.clicked.connect(self.export_msime)
        export_atok_button.clicked.connect(self.export_atok)
        export_skk_button.clicked.connect(self.export_skk)
        backup_onedrive_btn.clicked.connect(self.backup_to_onedrive)
        restore_onedrive_btn.clicked.connect(self.restore_from_onedrive)

        # 共有用クリップボード・QRコード
        export_clipboard_button = QPushButton("辞書をクリップボードにコピー")
        import_clipboard_button = QPushButton("クリップボードから辞書を読み込み")
        show_qr_button = QPushButton("QRコード表示")

        export_clipboard_button.clicked.connect(self.export_to_clipboard)
        import_clipboard_button.clicked.connect(self.import_from_clipboard)
        show_qr_button.clicked.connect(self.show_qr_code)

        export_layout = QVBoxLayout()
        export_layout.addWidget(export_google_button)
        export_layout.addWidget(export_msime_button)
        export_layout.addWidget(export_atok_button)
        export_layout.addWidget(export_skk_button)
        export_layout.addWidget(backup_onedrive_btn)
        export_layout.addWidget(restore_onedrive_btn)
        export_layout.addWidget(export_clipboard_button)
        export_layout.addWidget(import_clipboard_button)
        export_layout.addWidget(show_qr_button)
        export_layout.addStretch()

        export_widget = QWidget()
        export_widget.setLayout(export_layout)
        export_widget.setMaximumWidth(250)

        # 左右中央の3分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(export_widget)

        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)



    # ここから処理
    # ファイルリストの更新
    def refresh_file_list(self):
        self.file_list.clear()
        for fname in os.listdir(self.dictionary_dir):
            if fname.endswith(".txt"):
                self.file_list.addItem(fname)

    # ファイル選択時の処理
    def load_selected_file(self):
        items = self.file_list.selectedItems()
        if not items:
            self.entries = []
            self.table.setRowCount(0)
            self.current_file = None
            return
        fname = items[0].text()
        self.current_file = os.path.join(self.dictionary_dir, fname)
        self.entries = []
        with open(self.current_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("!"):
                    continue
                parts = line.strip().split('\t')
                if len(parts) == 3:
                    self.entries.append(tuple(parts))
        self.refresh_table()

    # テーブルを更新
    def refresh_table(self):
        self.table.setRowCount(len(self.entries))
        for i, (yomi, hyouki, hinshi) in enumerate(self.entries):
            self.table.setItem(i, 0, QTableWidgetItem(yomi))
            self.table.setItem(i, 1, QTableWidgetItem(hyouki))
            self.table.setItem(i, 2, QTableWidgetItem(hinshi))

    # ファイルを保存
    def save_current_file(self):
        if not self.current_file:
            return
        with open(self.current_file, "w", encoding="utf-8") as f:
            if "ime" in os.path.basename(self.current_file):
                f.write("!Microsoft IME Dictionary Tool\n")
            for yomi, hyouki, hinshi in self.entries:
                f.write(f"{yomi}\t{hyouki}\t{hinshi}\n")

    # 辞書に追加
    def add_entry(self):
        yomi = self.yomi_input.text().strip()
        hyouki = self.hyouki_input.text().strip()
        hinshi = self.hinshi_combo.currentText()
        if not yomi or not hyouki or not self.current_file:
            QMessageBox.warning(self, "入力エラー", "ファイル選択・読み・表記の全てを入力してください。")
            return
        self.entries.append((yomi, hyouki, hinshi))
        self.save_current_file()
        self.refresh_table()
        self.yomi_input.clear()
        self.hyouki_input.clear()

    # 単語編集
    def edit_entry(self):
        selected = self.table.currentRow()
        if selected < 0 or not self.current_file:
            QMessageBox.warning(self, "編集失敗", "編集する行を選択してください。")
            return
        yomi, hyouki, hinshi = self.entries[selected]
        self.yomi_input.setText(yomi)
        self.hyouki_input.setText(hyouki)
        self.hinshi_combo.setCurrentText(hinshi)
        del self.entries[selected]
        self.save_current_file()
        self.refresh_table()

    # 単語削除
    def delete_entry(self):
        selected = self.table.currentRow()
        if selected < 0 or not self.current_file:
            QMessageBox.warning(self, "削除失敗", "削除する行を選択してください。")
            return
        del self.entries[selected]
        self.save_current_file()
        self.refresh_table()

    # 新規ファイル作成
    def create_new_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, "新規辞書ファイル作成", self.dictionary_dir, "Text Files (*.txt)")
        if fname:
            if not fname.endswith(".txt"):
                fname += ".txt"
            with open(fname, "w", encoding="utf-8") as f:
                pass
            self.refresh_file_list()

    # ファイル削除
    def remove_selected_file(self):
        items = self.file_list.selectedItems()
        if not items:
            return
        fname = items[0].text()
        full_path = os.path.join(self.dictionary_dir, fname)
        os.remove(full_path)
        self.refresh_file_list()
        self.entries = []
        self.table.setRowCount(0)
        self.current_file = None

    # エクスプローラー開く
    def open_dictionary_folder(self):
        path = os.path.abspath(self.dictionary_dir)
        try:
            subprocess.Popen(f'explorer "{path}"')
        except Exception as e:
            QMessageBox.critical(self, "エクスプローラー起動失敗", f"エラー: {e}")

    # エクスポート機能群
    def export_google_mozc(self):
        if not self.current_file or not self.entries:
            QMessageBox.warning(self, "エクスポート失敗", "エクスポートする辞書ファイルを選択してください。")
            return
        base, _ = os.path.splitext(os.path.basename(self.current_file))
        fname = os.path.join(self.saved_dir, f"{base}_google_mozc.txt")
        with open(fname, "w", encoding="utf-8") as f:
            for yomi, hyouki, hinshi in self.entries:
                f.write(f"{yomi}\t{hyouki}\t{hinshi}\n")
        QMessageBox.information(self, "エクスポート完了", f"Google日本語入力/Mozc用TXTファイルを出力しました：\n{fname}")

    def export_msime(self):
        if not self.current_file or not self.entries:
            QMessageBox.warning(self, "エクスポート失敗", "エクスポートする辞書ファイルを選択してください。")
            return
        base, _ = os.path.splitext(os.path.basename(self.current_file))
        fname = os.path.join(self.saved_dir, f"{base}_msime.txt")
        import codecs
        with codecs.open(fname, "w", encoding="shift_jis") as f:
            for yomi, hyouki, hinshi in self.entries:
                f.write(f"{hyouki}\t{yomi}\t{hinshi}\n")
        QMessageBox.information(self, "エクスポート完了", f"Microsoft IME用TXTファイルを出力しました（Shift_JIS）：\n{fname}")

    def export_atok(self):
        if not self.current_file or not self.entries:
            QMessageBox.warning(self, "エクスポート失敗", "エクスポートする辞書ファイルを選択してください。")
            return
        base, _ = os.path.splitext(os.path.basename(self.current_file))
        fname = os.path.join(self.saved_dir, f"{base}_atok.csv")
        import codecs
        with codecs.open(fname, "w", encoding="shift_jis") as f:
            for yomi, hyouki, hinshi in self.entries:
                f.write(f"{hyouki},{yomi},{hinshi}\n")
        QMessageBox.information(self, "エクスポート完了", f"ATOK用CSVファイルを出力しました（Shift_JIS）：\n{fname}")

    def export_skk(self):
        if not self.current_file or not self.entries:
            QMessageBox.warning(self, "エクスポート失敗", "エクスポートする辞書ファイルを選択してください。")
            return
        base, _ = os.path.splitext(os.path.basename(self.current_file))
        fname = os.path.join(self.saved_dir, f"{base}_skk.dic")
        with open(fname, "w", encoding="utf-8") as f:
            for yomi, hyouki, _ in self.entries:
                f.write(f"{yomi} /{hyouki}/\n")
        QMessageBox.information(self, "エクスポート完了", f"SKK用テキストファイルを出力しました：\n{fname}")

    # OneDriveにバックアップ
    def backup_to_onedrive(self):
        if not self.current_file:
            QMessageBox.warning(self, "バックアップ失敗", "バックアップする辞書ファイルを選択してください。")
            return
        try:
            shutil.copy2(self.current_file, os.path.join(self.onedrive_dir, os.path.basename(self.current_file)))
            QMessageBox.information(self, "バックアップ完了", "OneDriveにバックアップしました。")
        except Exception as e:
            QMessageBox.critical(self, "バックアップ失敗", f"OneDriveへのバックアップに失敗しました。\n{e}")

    # OneDriveから復元
    def restore_from_onedrive(self):
        try:
            files = [f for f in os.listdir(self.onedrive_dir) if os.path.isfile(os.path.join(self.onedrive_dir, f))]
            if not files:
                QMessageBox.warning(self, "復元失敗", "OneDriveのバックアップフォルダにファイルがありません。")
                return

            fname, ok = QInputDialog.getItem(self, "復元するファイルを選択", "ファイル名:", files, 0, False)
            if not ok or not fname:
                return

            src = os.path.join(self.onedrive_dir, fname)
            dst = os.path.join(self.dictionary_dir, fname)

            shutil.copy2(src, dst)
            self.refresh_file_list()  # ファイルリストを更新
            QMessageBox.information(self, "復元完了", f"OneDriveから復元しました：\n{dst}")
        except Exception as e:
            QMessageBox.critical(self, "復元失敗", f"OneDriveからの復元に失敗しました。\n{e}")

    # クリップボードに辞書テキストをコピー
    def export_to_clipboard(self):
        if not self.entries or not self.current_file:
            QMessageBox.warning(self, "共有失敗", "エクスポートする辞書ファイルを選択してください。")
            return

        file_name = os.path.basename(self.current_file)
        text = f"{file_name}\n"
        for yomi, hyouki, hinshi in self.entries:
            text += f"{yomi}\t{hyouki}\t{hinshi}\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "コピー完了", f"{file_name} と辞書データをクリップボードにコピーしました。")

    # クリップボードから読み込み
    def import_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            QMessageBox.warning(self, "貼り付け失敗", "クリップボードにテキストがありません。")
            return

        lines = text.strip().splitlines()
        if not lines:
            QMessageBox.warning(self, "貼り付け失敗", "クリップボードに有効な行がありません。")
            return

        first_line = lines[0].strip()
        if not (first_line.endswith(".txt") or first_line.endswith("）")):
            QMessageBox.warning(self, "ファイル名エラー", "1行目にファイル名（例: xxx.txt）を含めてください。")
            return

        import re
        match = re.search(r"\(?([^\s()]+\.txt)\)?", first_line)
        if not match:
            QMessageBox.warning(self, "ファイル名抽出失敗", "先頭行からファイル名が抽出できませんでした。")
            return
        file_name = match.group(1)
        self.current_file = os.path.join(self.dictionary_dir, file_name)

        new_entries = []
        for line in lines[1:]:
            parts = line.strip().split('\t')
            if len(parts) == 3:
                new_entries.append(tuple(parts))

        if not new_entries:
            QMessageBox.warning(self, "貼り付け失敗", "有効な辞書データが見つかりませんでした。")
            return

        ret = QMessageBox.question(
            self, "辞書データ読み込み",
            f"{file_name} に {len(new_entries)} 件のデータを上書き保存します。よろしいですか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        self.entries = new_entries
        self.save_current_file()
        self.refresh_table()
        self.refresh_file_list()

        QMessageBox.information(self, "読み込み完了", f"{file_name} を作成または上書きし、辞書データをインポートしました。")

    # QRコードを表示
    def show_qr_code(self):
        if not self.entries:
            QMessageBox.warning(self, "QRコード生成失敗", "エクスポートする辞書データがありません。")
            return

        text = ""
        for yomi, hyouki, hinshi in self.entries:
            text += f"{yomi}\t{hyouki}\t{hinshi}\n"

        if self.current_file:
            base_name = os.path.splitext(os.path.basename(self.current_file))[0]
        else:
            base_name = "qr_code"

        dlg = QRCodeDialog(text, self, filename=base_name)
        dlg.exec()



# ここからMainWindow抜ける
# QRコードの表示ウィンドウ
class QRCodeDialog(QDialog):
    def __init__(self, text, parent=None, filename="qr_code"):
        super().__init__(parent)
        self.setWindowTitle("QRコード表示")
        self.setMinimumSize(300, 400)

        self.qr_img = qrcode.make(text).convert('RGB')
        qt_img = ImageQt(self.qr_img)
        pix = QPixmap.fromImage(QImage(qt_img))

        self.label = QLabel()
        self.label.setPixmap(pix.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio))

        self.filename = filename

        save_button = QPushButton("QRコードを保存")
        save_button.clicked.connect(self.save_qr_code)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(save_button)
        self.setLayout(layout)

    # QRコードを保存できるようにする処理
    def save_qr_code(self):
        downloads = str(Path.home() / "Downloads")
        save_name = f"{self.filename}.png"
        save_path, _ = QFileDialog.getSaveFileName(self, "QRコードを保存", os.path.join(downloads, save_name), "PNG Files (*.png)")
        if save_path:
            self.qr_img.save(save_path)
            QMessageBox.information(self, "保存完了", f"QRコードを保存しました：\n{save_path}")
