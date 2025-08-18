#!/bin/bash
set -e

if ! command -v node >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y nodejs npm
fi
# 全局安装 Claude Code
npm install -g @anthropic-ai/claude-code
