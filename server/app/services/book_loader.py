import os
import re

BOOKS_DIR = "books"  # 书籍存放目录


def get_all_books():
    """扫描目录，返回所有书籍的列表（不含内容，只含元数据）"""
    books = []
    if not os.path.exists(BOOKS_DIR):
        os.makedirs(BOOKS_DIR)

    for filename in os.listdir(BOOKS_DIR):
        if filename.endswith(".txt"):
            # 使用文件名作为 ID 和 标题 (去除 .txt)
            book_id = filename
            title = filename.replace(".txt", "")
            books.append({
                "id": book_id,
                "title": title,
                "cover": "📘"  # 以后可以换成图片 URL
            })
    return books


def parse_book_content(book_filename):
    """读取具体 txt 文件，解析章节和段落"""
    file_path = os.path.join(BOOKS_DIR, book_filename)

    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 数据结构
    book_data = {
        "title": book_filename.replace(".txt", ""),
        "chapters": []
    }

    # 1. 正则匹配章节 (假设格式为: === 章节名 ===)
    # 如果你的txt没有这种标记，可以改正则，比如 r"第[一二三四五六七八九十]+章"
    chapter_pattern = r"===\s*(.*?)\s*==="
    parts = re.split(chapter_pattern, text)

    # re.split 的结果通常是 [前言, 标题1, 内容1, 标题2, 内容2...]
    # 如果第一段不是以 === 开头，parts[0] 是前言或第一章内容

    if len(parts) < 2:
        # 没找到章节标记，把全文当做一章
        content = text.strip()
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        book_data["chapters"].append({
            "id": 1,
            "title": "全书内容",
            "content": paragraphs
        })
    else:
        # 处理分割后的内容
        current_chapter_id = 1
        # parts[0] 通常是空或者书名前的废话，跳过或作为序言
        # 从索引 1 开始，两两一组 (标题, 内容)
        for i in range(1, len(parts), 2):
            chapter_title = parts[i].strip()
            chapter_content_raw = parts[i + 1]

            # 按换行符分割段落，并过滤空行
            paragraphs = [p.strip() for p in chapter_content_raw.split('\n') if p.strip()]

            book_data["chapters"].append({
                "id": current_chapter_id,
                "title": chapter_title,
                "content": paragraphs
            })
            current_chapter_id += 1

    return book_data