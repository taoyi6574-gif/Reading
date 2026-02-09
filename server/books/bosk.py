def format_robinson_document(input_text, output_file="格式化_鲁滨孙漂流记.txt"):
    # 定义章节标题列表（从文档中提取的核心章节名）
    chapters = [
        "版权信息",
        "初尝航海的甘苦",
        "流落到无人岛上",
        "与世隔绝的生活",
        "环岛旅行",
        "发现野人行踪",
        "星期五的到来",
        "惊险的拯救行动",
        "回到了英国",
        "结束漂流的生涯"
    ]

    # 初始化格式化后的内容列表
    formatted_content = []

    # 处理版权信息（文档开头部分）
    content_lines = input_text.split("\n")
    current_line_idx = 0

    # 提取并格式化版权信息
    copyright_lines = []
    while current_line_idx < len(content_lines):
        line = content_lines[current_line_idx].strip()
        if line in chapters[1:]:  # 遇到下一章标题则停止
            break
        if line:  # 保留非空行
            copyright_lines.append(line)
        current_line_idx += 1
    formatted_content.append(f"=== {chapters[0]} ===")
    formatted_content.append("\n".join(copyright_lines))
    formatted_content.append("")  # 段落间隔

    # 处理后续章节
    for chapter in chapters[1:]:
        # 查找当前章节的起始位置
        while current_line_idx < len(content_lines):
            line = content_lines[current_line_idx].strip()
            if line == chapter:
                break
            current_line_idx += 1
        if current_line_idx >= len(content_lines):
            break

        # 提取当前章节内容
        chapter_lines = []
        current_line_idx += 1  # 跳过章节标题行
        next_chapter_idx = chapters.index(chapter) + 1
        next_chapter = chapters[next_chapter_idx] if next_chapter_idx < len(chapters) else None

        while current_line_idx < len(content_lines):
            line = content_lines[current_line_idx].strip()
            # 遇到下一章标题或文档结束则停止
            if next_chapter and line == next_chapter:
                break
            # 处理段落：非空行保留，空行视为段落分隔
            if line:
                chapter_lines.append(line)
            else:
                if chapter_lines and chapter_lines[-1] != "":
                    chapter_lines.append("")  # 段落间隔
            current_line_idx += 1

        # 清理多余的空行
        cleaned_chapter = []
        for line in chapter_lines:
            if line == "" and cleaned_chapter and cleaned_chapter[-1] == "":
                continue
            cleaned_chapter.append(line)
        # 移除末尾多余空行
        while cleaned_chapter and cleaned_chapter[-1] == "":
            cleaned_chapter.pop()

        # 添加章节标题和内容
        formatted_content.append(f"=== {chapter} ===")
        formatted_content.append("\n".join(cleaned_chapter))
        formatted_content.append("")  # 章节间间隔

    # 合并所有内容并写入文件
    final_content = "\n".join(formatted_content).rstrip("\n")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"文档格式化完成，已保存到：{output_file}")


# 读取原始文档内容（将此处替换为你的文档实际路径）
input_file_path = "鲁滨孙漂流记.txt"
with open(input_file_path, "r", encoding="utf-8") as f:
    raw_content = f.read()

# 执行格式化
format_robinson_document(raw_content)