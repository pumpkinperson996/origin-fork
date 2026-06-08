import asyncio
import sys

import win32gui
from PIL import Image

from winrt.windows.graphics.imaging import (
    BitmapPixelFormat,
    SoftwareBitmap,
)
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.security.cryptography import CryptographicBuffer

from ocrcheck import capture_window


WINDOW_CLASS = "Qt680QWindowIcon"
WINDOW_TITLE_KEYWORDS = ("绝区零 一条龙",)
KEYWORDS = ("启动一条龙", "开始 F9", "开始")
FORBIDDEN_STATUS_KEYWORDS = ("暂停", "继续", "停止")


def sanitize(value: str) -> str:
    return value.replace("|", " ").replace("\r", " ").replace("\n", " ").strip()


def normalize(value: str) -> str:
    return "".join(value.split()).upper()


def find_window_by_class(class_name: str):
    matches = []

    def cb(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            if win32gui.GetClassName(hwnd) != class_name:
                return
            title = win32gui.GetWindowText(hwnd)
            if not any(keyword in title for keyword in WINDOW_TITLE_KEYWORDS):
                return
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            if right - left > 100 and bottom - top > 100:
                matches.append(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(cb, None)
    return matches[0] if matches else None


def rect_values(rect):
    return (
        float(getattr(rect, "x", getattr(rect, "X", 0))),
        float(getattr(rect, "y", getattr(rect, "Y", 0))),
        float(getattr(rect, "width", getattr(rect, "Width", 0))),
        float(getattr(rect, "height", getattr(rect, "Height", 0))),
    )


def union_rects(rects):
    if not rects:
        return None
    left = min(r[0] for r in rects)
    top = min(r[1] for r in rects)
    right = max(r[0] + r[2] for r in rects)
    bottom = max(r[1] + r[3] for r in rects)
    return left, top, right - left, bottom - top


def line_text(line) -> str:
    text = getattr(line, "text", "")
    if text:
        return text
    return "".join(getattr(word, "text", "") for word in getattr(line, "words", []))


def line_rect(line):
    rects = []
    for word in getattr(line, "words", []):
        rect = rect_values(word.bounding_rect)
        if rect[2] > 0 and rect[3] > 0:
            rects.append(rect)
    return union_rects(rects)


def keyword_matches(keyword: str, text: str) -> bool:
    keyword_norm = normalize(keyword)
    text_norm = normalize(text)

    if keyword_norm == "开始":
        return text_norm == "开始" or text_norm.startswith("开始F")
    return keyword_norm in text_norm


def contains_forbidden_status(text: str) -> bool:
    text_norm = normalize(text)
    if any(normalize(keyword) in text_norm for keyword in KEYWORDS):
        return False
    return any(normalize(keyword) in text_norm for keyword in FORBIDDEN_STATUS_KEYWORDS)


async def recognize_image(img: Image.Image):
    img_bgra = img.convert("RGBA")
    r, g, b, a = img_bgra.split()
    img_bgra = Image.merge("RGBA", (b, g, r, a))
    pixel_bytes = img_bgra.tobytes()

    buf = CryptographicBuffer.create_from_byte_array(pixel_bytes)
    soft_bmp = SoftwareBitmap.create_copy_from_buffer(
        buf, BitmapPixelFormat.BGRA8, img.width, img.height
    )

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        return None

    return await engine.recognize_async(soft_bmp)


def find_text_match(result):
    lines = list(getattr(result, "lines", []))
    for keyword in KEYWORDS:
        for line in lines:
            text = line_text(line)
            if contains_forbidden_status(text):
                continue
            if not keyword_matches(keyword, text):
                continue
            rect = line_rect(line)
            if rect is None:
                continue
            return keyword, text, rect
    return None


def search_regions(img: Image.Image):
    w, h = img.size
    right_w = min(620, w)
    bottom_h = min(280, h)
    yield "bottom_right", img.crop((w - right_w, h - bottom_h, w, h)), w - right_w, h - bottom_h
    yield "full", img, 0, 0


async def main(hwnd_arg: str | None = None) -> str:
    hwnd = None
    if hwnd_arg:
        try:
            hwnd = int(hwnd_arg, 0)
        except ValueError:
            return "ERROR|0|0|invalid hwnd"
    else:
        hwnd = find_window_by_class(WINDOW_CLASS)

    if not hwnd or not win32gui.IsWindow(hwnd):
        return "NO_WINDOW|0|0|"

    img = capture_window(hwnd)
    if img is None:
        return "NO_WINDOW|0|0|"

    win_left, win_top, _, _ = win32gui.GetWindowRect(hwnd)
    preview = ""
    for _, region_img, offset_x, offset_y in search_regions(img):
        result = await recognize_image(region_img)
        if result is None:
            return "NO_ENGINE|0|0|"
        if not preview:
            preview = sanitize(getattr(result, "text", ""))[:120]

        match = find_text_match(result)
        if match is None:
            continue

        _, matched_text, rect = match
        x, y, w, h = rect
        screen_x = int(round(win_left + offset_x + x + w / 2))
        screen_y = int(round(win_top + offset_y + y + h / 2))
        return f"FOUND|{screen_x}|{screen_y}|{sanitize(matched_text)}"

    return f"NOT_FOUND|0|0|{preview}"


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else None
    hwnd = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        output = asyncio.run(main(hwnd))
    except Exception as exc:
        output = f"ERROR|0|0|{sanitize(str(exc))}"

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)
