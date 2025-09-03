#!/bin/bash
file="$1"

# 创建临时文件
temp_file=$(mktemp)

# 处理文件：去除行尾空白，删除末尾多余空行
# 使用 python 来精确处理，避免 sed 的兼容性问题
python3 -c "
import sys
with open('$file', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 去除每行末尾的空白字符
lines = [line.rstrip() + '\n' for line in lines]

# 删除文件末尾的空行
while lines and lines[-1].strip() == '':
    lines.pop()

# 确保文件以一个空行结尾
if lines and lines[-1] != '\n':
    lines.append('\n')

with open('$temp_file', 'w', encoding='utf-8') as f:
    f.writelines(lines)
"

# 替换原文件
mv "$temp_file" "$file"
