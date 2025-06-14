from pathlib import Path

class DictionaryManager:
    def __init__(self, google_path, ime_path):
        self.google_path = Path(google_path)
        self.ime_path = Path(ime_path)
        self.google_path.parent.mkdir(parents=True, exist_ok=True)
        self.ime_path.parent.mkdir(parents=True, exist_ok=True)

    def export_google(self, entries):
        with self.google_path.open("w", encoding="utf-8") as f:
            for yomi, hyouki, hinshi in entries:
                f.write(f"{yomi}\t{hyouki}\t{hinshi}\n")

    def export_ime(self, entries):
        with self.ime_path.open("w", encoding="utf-8") as f:
            f.write("!Microsoft IME Dictionary Tool\n")
            for yomi, hyouki, hinshi in entries:
                f.write(f"{yomi}\t{hyouki}\t{hinshi}\n")