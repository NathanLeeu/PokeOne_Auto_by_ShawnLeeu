import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab, Image, ImageTk
import pygetwindow as gw
import time
import tkinter as tk
import json

# Đường dẫn tới tệp center.png
CENTER_IMAGE_PATH = r"D:\PokeOne\PokeBot\Bot\Image\center.png"

# Đường dẫn tới tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Đường dẫn tới tệp moves.json
MOVES_JSON_PATH = r"D:\PokeOne\PokeBot\Bot\Database\moves.json"

def load_moves_data():
    try:
        with open(MOVES_JSON_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Không tìm thấy tệp {MOVES_JSON_PATH}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Lỗi phân tích cú pháp JSON: {e}")
        return {}

def focus_pokeone_window():
    print("Đang tập trung vào cửa sổ PokeOne...")
    windows = gw.getWindowsWithTitle('PokeOne')
    if windows:
        window = windows[0]
        if not window.isActive:
            window.activate()
        window.restore()  # Phục hồi cửa sổ nếu nó bị thu nhỏ
        window.maximize()  # Tối ưu hóa cửa sổ để có đủ không gian nhìn thấy
        print("Đã kích hoạt cửa sổ PokeOne.")
    else:
        print("Không tìm thấy cửa sổ PokeOne. Vui lòng đảm bảo rằng trò chơi đang chạy.")

def capture_screen(region=None):
    print("Đang chụp màn hình...")
    if region:
        x1, y1, x2, y2 = region
        return np.array(ImageGrab.grab(bbox=(x1, y1, x2, y2)))
    return np.array(ImageGrab.grab())

def detect_center_circle(screen, template_path):
    print("Đang phát hiện vòng tròn trung tâm...")
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"Không thể tải hình ảnh mẫu từ {template_path}")
        return None

    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val > 0.8:
        print("Đã phát hiện vòng tròn trung tâm.")
        return max_loc
    print("Không phát hiện được vòng tròn trung tâm.")
    return None

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

def extract_text_around_center(screen, center_pos):
    print("Đang trích xuất văn bản xung quanh trung tâm...")
    h, w, _ = screen.shape
    skill_regions = [
    (center_pos[0] - 160, center_pos[1] - 50, center_pos[0] - 40, center_pos[1] - 10),  # Top-left
    (center_pos[0] + 50, center_pos[1] - 50, center_pos[0] + 170, center_pos[1] - 10),  # Top-right
    (center_pos[0] - 160, center_pos[1] + 20, center_pos[0] - 40, center_pos[1] + 80),  # Bot-left
    (center_pos[0] + 50, center_pos[1] + 20, center_pos[0] + 170, center_pos[1] + 80),  # Bot-right

       (center_pos[0] - 170, center_pos[1] - 25, center_pos[0] - 30, center_pos[1] + 15),  # Top-left PP
        (center_pos[0] + 50, center_pos[1] - 25, center_pos[0] + 170, center_pos[1] + 15),  # Top-right PP
        (center_pos[0] - 170, center_pos[1] + 55, center_pos[0] - 30 , center_pos[1] + 97),  # Bot-left PP
        (center_pos[0] + 50, center_pos[1] + 40, center_pos[0] + 170, center_pos[1] + 97),  # Bot-right PP
    ]

    skill_texts = []
    for region in skill_regions:
        x1, y1, x2, y2 = region
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        skill_img = screen[y1:y2, x1:x2]
        preprocessed_img = preprocess_image(skill_img)
        text = pytesseract.image_to_string(preprocessed_img, config='--psm 7').strip()
        skill_texts.append(text)
    
    return skill_texts

def find_skill_info(skill_name, moves_data):
    for move in moves_data:
        if move['name'].lower() == skill_name.lower():
            return move
    return None

def display_image(image, title='Image'):
    root = tk.Tk()
    root.title(title)
    cv_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(cv_image)
    tk_image = ImageTk.PhotoImage(pil_image)
    
    label = tk.Label(root, image=tk_image)
    label.pack()
    
    root.after(500, root.destroy)  # Đóng cửa sổ sau 0.5 giây
    root.mainloop()

def main_loop():
    moves_data = load_moves_data()
    while True:
        try:
            focus_pokeone_window()
            screen = capture_screen()
            center_pos = detect_center_circle(screen, CENTER_IMAGE_PATH)
            if center_pos:
                skill_texts = extract_text_around_center(screen, center_pos)
                print("Tên các kỹ năng được phát hiện:")
                for text in skill_texts:
                    if text:
                        skill_info = find_skill_info(text, moves_data)
                        if skill_info:
                            print(json.dumps(skill_info, indent=2, ensure_ascii=False))
                        else:
                            print(f"Không tìm thấy thông tin cho kỹ năng: {text}")
            else:
                print("Không tìm thấy vòng tròn trung tâm. Bỏ qua việc trích xuất kỹ năng.")
        except Exception as e:
            print(f"Đã xảy ra lỗi: {e}")
        time.sleep(5)  # Đợi 5 giây trước khi lặp lại

if __name__ == "__main__":
    main_loop()
