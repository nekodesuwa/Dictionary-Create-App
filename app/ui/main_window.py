from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QListWidget, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt
import os
import subprocess

from app.logic.drive_sync import upload_file_to_drive

class MainWindow(QWidget):
    def __init__(self, dictionary_dir):
        super().__init__()
        self.setWindowTitle("辞書ファイル管理ツール")
        self.dictionary_dir = dictionary_dir
        os.makedirs(self.dictionary_dir, exist_ok=True)

        # 左側
        # dictionaryのファイル一覧
        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.load_selected_file)

        # ファイル操作ボタン
        new_file_button = QPushButton("新規辞書ファイル作成")
        remove_file_button = QPushButton("辞書ファイル削除")
        open_folder_button = QPushButton("辞書フォルダを開く")
        new_file_button.clicked.connect(self.create_new_file)
        remove_file_button.clicked.connect(self.remove_selected_file)
        open_folder_button.clicked.connect(self.open_dictionary_folder)

        # ボタン横並び
        file_btns = QHBoxLayout()
        file_btns.addWidget(new_file_button)
        file_btns.addWidget(remove_file_button)

        # 単語編集フォーム
        self.yomi_input = QLineEdit()
        self.yomi_input.setMaxLength(60)  # 60文字制限
        self.hyouki_input = QLineEdit()
        self.hyouki_input.setMaxLength(60)

        # 品詞選択できるよ
        self.hinshi_combo = QComboBox()
        self.hinshi_list = [
            "名詞", "動詞", "形容詞", "副詞", "連体詞", "接続詞", "感動詞", "記号", "カスタム名詞"
        ]
        self.hinshi_combo.addItems(self.hinshi_list)
        self.hinshi_combo.setCurrentText("名詞")

        # 辞書追加ボタン
        add_button = QPushButton("辞書に追加")
        add_button.clicked.connect(self.add_entry)

        # 入力フォームのレイアウト
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("読み"))
        input_layout.addWidget(self.yomi_input)
        input_layout.addWidget(QLabel("表記"))
        input_layout.addWidget(self.hyouki_input)
        input_layout.addWidget(QLabel("品詞"))
        input_layout.addWidget(self.hinshi_combo)
        input_layout.addWidget(add_button)

        # その他レイアウト
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("辞書ファイル一覧"))
        left_layout.addWidget(self.file_list)
        left_layout.addLayout(file_btns)
        left_layout.addWidget(open_folder_button)
        left_layout.addSpacing(20)
        left_layout.addLayout(input_layout)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)



        # 右側
        # テーブルと編集・削除ボタン
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["読み", "表記", "品詞"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumWidth(350)

        edit_button = QPushButton("編集")
        delete_button = QPushButton("削除")
        edit_button.clicked.connect(self.edit_entry)
        delete_button.clicked.connect(self.delete_entry)

        table_btns = QHBoxLayout()
        table_btns.addWidget(edit_button)
        table_btns.addWidget(delete_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.table)
        right_layout.addLayout(table_btns)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)



        # 全体のレイアウト
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([350, 500])  # 初期幅
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # 初期化だよ
        self.entries = []
        self.current_file = None
        self.refresh_file_list()



    # こっから処理系
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

    #  ファイルを保存
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