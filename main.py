# -*- coding: utf-8 -*-
"""
Yumiko - Cô AI dễ thương chuyên code + kiểm tra ảnh
Chạy online (Claude API) khi có wifi, offline (rule-based) khi không có mạng.
"""

import os
import json
import base64
import socket
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.storage.jsonstore import JsonStore

try:
    import requests
except ImportError:
    requests = None

try:
    from plyer import filechooser
except ImportError:
    filechooser = None

try:
    from PIL import Image, ImageFilter, ImageStat
except ImportError:
    Image = None

Window.clearcolor = (1, 0.94, 0.97, 1)  # nền hồng pastel

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(APP_DIR, "yumiko_store.json")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MODEL_NAME = "claude-sonnet-4-6"

YUMIKO_SYSTEM_PROMPT = (
    "Bạn tên là Yumiko, một trợ lý AI dễ thương, thân thiện, nói chuyện tự nhiên "
    "bằng tiếng Việt, xưng 'Yumiko' hoặc 'mình', gọi người dùng là 'cậu'. "
    "Bạn là chuyên gia lập trình: giải thích rõ ràng, ngắn gọn, có code mẫu khi cần. "
    "Giữ giọng điệu ấm áp, tích cực nhưng vẫn chính xác về mặt kỹ thuật."
)

KV = """
ScreenManager:
    HomeScreen:
    CodeScreen:
    PhotoScreen:
    SettingsScreen:

<RoundedButton@Button>:
    background_normal: ''
    background_color: 0.98, 0.6, 0.75, 1
    color: 1,1,1,1
    font_size: '16sp'
    size_hint_y: None
    height: '48dp'

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "16dp"

        Label:
            text: "( ˘ ³˘) Yumiko"
            font_size: "30sp"
            color: 0.8, 0.2, 0.45, 1
            size_hint_y: None
            height: "60dp"

        Label:
            text: root.status_text
            color: 0.4,0.4,0.4,1
            size_hint_y: None
            height: "30dp"

        Label:
            text: "Chào cậu! Yumiko có thể giúp cậu code và kiểm tra ảnh nè~"
            color: 0.3,0.3,0.3,1
            size_hint_y: None
            height: "60dp"
            text_size: self.width, None
            halign: "center"

        RoundedButton:
            text: "💻 Trợ lý Code"
            on_release: app.root.current = "code"

        RoundedButton:
            text: "🖼️ Kiểm tra ảnh"
            on_release: app.root.current = "photo"

        RoundedButton:
            text: "⚙️ Cài đặt API Key"
            on_release: app.root.current = "settings"

<CodeScreen>:
    name: "code"
    BoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "10dp"

        BoxLayout:
            size_hint_y: None
            height: "40dp"
            RoundedButton:
                text: "< Quay lại"
                size_hint_x: None
                width: "110dp"
                on_release: app.root.current = "home"
            Label:
                text: "Trợ lý Code - Yumiko"
                color: 0.8,0.2,0.45,1

        ScrollView:
            Label:
                id: code_output
                text: root.output_text
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                color: 0.2,0.2,0.2,1
                halign: "left"
                valign: "top"
                padding: "8dp", "8dp"

        TextInput:
            id: code_input
            hint_text: "Hỏi Yumiko về code..."
            size_hint_y: None
            height: "80dp"
            multiline: True

        RoundedButton:
            text: "Gửi cho Yumiko"
            on_release: root.ask_yumiko(code_input.text)

<PhotoScreen>:
    name: "photo"
    BoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "10dp"

        BoxLayout:
            size_hint_y: None
            height: "40dp"
            RoundedButton:
                text: "< Quay lại"
                size_hint_x: None
                width: "110dp"
                on_release: app.root.current = "home"
            Label:
                text: "Kiểm tra ảnh - Yumiko"
                color: 0.8,0.2,0.45,1

        Image:
            id: preview_img
            size_hint_y: 0.4

        RoundedButton:
            text: "Chọn ảnh"
            on_release: root.pick_image()

        ScrollView:
            Label:
                id: photo_output
                text: root.output_text
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                color: 0.2,0.2,0.2,1
                halign: "left"
                valign: "top"
                padding: "8dp", "8dp"

<SettingsScreen>:
    name: "settings"
    BoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "12dp"

        BoxLayout:
            size_hint_y: None
            height: "40dp"
            RoundedButton:
                text: "< Quay lại"
                size_hint_x: None
                width: "110dp"
                on_release: app.root.current = "home"
            Label:
                text: "Cài đặt"
                color: 0.8,0.2,0.45,1

        Label:
            text: "Nhập Claude API Key (chỉ lưu trên máy cậu):"
            color: 0.3,0.3,0.3,1
            size_hint_y: None
            height: "40dp"
            text_size: self.width, None

        TextInput:
            id: api_key_input
            hint_text: "sk-ant-..."
            password: True
            multiline: False
            size_hint_y: None
            height: "48dp"
            text: root.current_key

        RoundedButton:
            text: "Lưu"
            on_release: root.save_key(api_key_input.text)

        Label:
            text: root.save_msg
            color: 0.2,0.6,0.3,1
            size_hint_y: None
            height: "30dp"
"""


def is_online(timeout=2.5):
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("8.8.8.8", 53))
        s.close()
        return True
    except Exception:
        return False


def get_store():
    return JsonStore(STORE_PATH)


def get_api_key():
    store = get_store()
    if store.exists("settings"):
        return store.get("settings").get("api_key", "")
    return ""


class HomeScreen(Screen):
    status_text = "Đang kiểm tra kết nối..."

    def on_pre_enter(self):
        threading.Thread(target=self._check_status, daemon=True).start()

    def _check_status(self):
        online = is_online()
        self._set_status(online)

    @mainthread
    def _set_status(self, online):
        self.status_text = "🟢 Online - Yumiko thông minh full sức" if online else "🔴 Offline - Yumiko chạy chế độ nhẹ"


class CodeScreen(Screen):
    output_text = "Yumiko sẵn sàng giúp cậu code nè! Hỏi gì cũng được~"

    def ask_yumiko(self, question):
        question = (question or "").strip()
        if not question:
            return
        self.output_text = "Yumiko đang suy nghĩ... (｡•́︿•̀｡)"
        threading.Thread(target=self._process, args=(question,), daemon=True).start()

    def _process(self, question):
        api_key = get_api_key()
        if is_online() and api_key and requests:
            try:
                answer = self._ask_claude(question, api_key)
                self._set_output("Cậu hỏi: {}\n\nYumiko: {}".format(question, answer))
                return
            except Exception as e:
                self._set_output("Yumiko gặp lỗi khi gọi API: {}\n\nChuyển sang chế độ offline nhé~".format(e))

        answer = self._offline_answer(question)
        self._set_output("Cậu hỏi: {}\n\nYumiko (offline): {}".format(question, answer))

    def _ask_claude(self, question, api_key):
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        payload = {
            "model": MODEL_NAME,
            "max_tokens": 1024,
            "system": YUMIKO_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": question}],
        }
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=30)
        data = resp.json()
        if "content" in data:
            texts = [b.get("text", "") for b in data["content"] if b.get("type") == "text"]
            return "\n".join(texts).strip() or "(không có phản hồi)"
        return "Lỗi API: {}".format(data.get("error", data))

    def _offline_answer(self, question):
        q = question.lower()
        snippets = {
            "python hello world": 'print("Hello World")',
            "for python": "for i in range(10):\n    print(i)",
            "while python": "i = 0\nwhile i < 10:\n    print(i)\n    i += 1",
            "class python": "class Animal:\n    def __init__(self, name):\n        self.name = name\n\n    def speak(self):\n        print(f\"{self.name} kêu!\")",
            "function python": "def cong(a, b):\n    return a + b",
            "java hello world": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello World");\n    }\n}',
            "javascript hello world": 'console.log("Hello World");',
            "c++ hello world": '#include <iostream>\nint main() {\n    std::cout << "Hello World";\n    return 0;\n}',
        }
        for key, code in snippets.items():
            if all(w in q for w in key.split()):
                return "Đây là ví dụ:\n\n{}".format(code)

        if "python" in q and ("kiểm tra" in q or "lỗi" in q or "check" in q):
            return "Ở chế độ offline, Yumiko chỉ kiểm tra được cú pháp Python cơ bản. Dán code Python vào ô chat, Yumiko sẽ thử compile thử xem có lỗi cú pháp không nhé."

        try:
            compile(question, "<snippet>", "exec")
            return "Yumiko thử compile đoạn này như code Python và không thấy lỗi cú pháp! 🎉"
        except SyntaxError as e:
            return "Nếu đây là code Python thì có vẻ lỗi cú pháp ở dòng {}: {}".format(e.lineno, e.msg)
        except Exception:
            pass

        return (
            "Yumiko đang offline nên chỉ trả lời được câu hỏi cơ bản/mẫu code thông dụng "
            "(hello world, for, while, class, function bằng Python/Java/JS/C++). "
            "Kết nối wifi để Yumiko thông minh hơn nha cậu~"
        )

    @mainthread
    def _set_output(self, text):
        self.output_text = text


class PhotoScreen(Screen):
    output_text = "Chọn một tấm ảnh để Yumiko kiểm tra nhé~"
    current_path = None

    def pick_image(self):
        if filechooser:
            try:
                filechooser.open_file(
                    on_selection=self._on_file_selected,
                    filters=[("Images", "*.png;*.jpg;*.jpeg")],
                )
                return
            except Exception:
                pass
        self.output_text = "Không mở được trình chọn ảnh trên thiết bị này."

    def _on_file_selected(self, selection):
        if not selection:
            return
        path = selection[0]
        self.current_path = path
        self.ids.preview_img.source = path
        self.output_text = "Đang phân tích ảnh..."
        threading.Thread(target=self._process, args=(path,), daemon=True).start()

    def _process(self, path):
        api_key = get_api_key()
        if is_online() and api_key and requests:
            try:
                answer = self._ask_claude_vision(path, api_key)
                self._set_output("Yumiko: {}".format(answer))
                return
            except Exception as e:
                self._set_output("Lỗi khi gọi API ({}), chuyển sang offline nhé~".format(e))

        answer = self._offline_analysis(path)
        self._set_output("Yumiko (offline): {}".format(answer))

    def _ask_claude_vision(self, path, api_key):
        with open(path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        media_type = "image/png" if path.lower().endswith("png") else "image/jpeg"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        payload = {
            "model": MODEL_NAME,
            "max_tokens": 600,
            "system": YUMIKO_SYSTEM_PROMPT,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
                    {"type": "text", "text": "Hãy kiểm tra và mô tả tấm ảnh này giúp mình, nhận xét về chất lượng, bố cục, và nội dung."}
                ]
            }]
        }
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=40)
        data = resp.json()
        if "content" in data:
            texts = [b.get("text", "") for b in data["content"] if b.get("type") == "text"]
            return "\n".join(texts).strip()
        return "Lỗi API: {}".format(data.get("error", data))

    def _offline_analysis(self, path):
        if not Image:
            return "Thiếu thư viện Pillow, không phân tích được offline."
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            return "Không mở được ảnh: {}".format(e)

        w, h = img.size
        stat = ImageStat.Stat(img)
        r, g, b = stat.mean
        brightness = (r + g + b) / 3

        gray = img.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        sharpness = edge_stat.stddev[0]

        if brightness < 60:
            bright_desc = "khá tối"
        elif brightness > 190:
            bright_desc = "khá sáng/dư sáng"
        else:
            bright_desc = "độ sáng ổn"

        blur_desc = "có thể bị mờ" if sharpness < 15 else "khá nét"

        dominant = "đỏ" if r >= g and r >= b else ("xanh lá" if g >= r and g >= b else "xanh dương")

        return (
            "Kích thước {}x{}px. Độ sáng trung bình {:.0f}/255 ({}). "
            "Độ sắc nét ước tính: {:.1f} ({}). Tông màu chủ đạo nghiêng về {}."
        ).format(w, h, brightness, bright_desc, sharpness, blur_desc, dominant)

    @mainthread
    def _set_output(self, text):
        self.output_text = text


class SettingsScreen(Screen):
    current_key = ""
    save_msg = ""

    def on_pre_enter(self):
        self.current_key = get_api_key()
        self.save_msg = ""

    def save_key(self, key):
        key = (key or "").strip()
        store = get_store()
        store.put("settings", api_key=key)
        self.save_msg = "Đã lưu! Yumiko sẽ dùng key này khi có wifi."


class YumikoApp(App):
    def build(self):
        self.title = "Yumiko"
        return Builder.load_string(KV)


if __name__ == "__main__":
    YumikoApp().run()
