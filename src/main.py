import os
import json
import sys
import re
from urllib.parse import quote
from pathlib import Path

# 目标目录
DEFAULT_TARGET_DIR = "/mnt/c/Users/asus/Documents/GitHub/JNU-EXAM"
SEPARATOR = "__"

# Alist/蓝奏云 配置
ALIST_DOMAIN = ""
MOUNT_PATH_PREFIX = "/d/lanzou" # alist需要关掉签名，并在最前面加上/d

SOURCES = [
    {
        "name": "Github",
        "key": "github_raw_url",
        "base": "https://raw.githubusercontent.com/gubaiovo/JNU-EXAM/main",
        "type": "tree",
        "enabled": True
    },
    {
        "name": "Gitee",
        "key": "gitee_raw_url",
        "base": "https://gitee.com/gubaiovo/jnu-exam/raw/main",
        "type": "tree",
        "enabled": False
    },
    {
        "name": "CloudFlare R2",
        "key": "cf_url",
        "base": "https://jnuexam.xyz", 
        "type": "tree",
        "enabled": True
    },
    {
        "name": "LanzouCloud",
        "key": "lanzou_url",
        "base": f"{ALIST_DOMAIN}{MOUNT_PATH_PREFIX}",
        "type": "flat",
        "enabled": True
    }
]
DEFAULT_IGNORES = [
    ".git", ".gitignore", "upload.txt", "directory_structure.json", 
    ".idea", ".vscode", "__pycache__", ".upload_cache", "tools"
]

def sanitize_name(name):
    name = re.sub(r'\s+', '', name)
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    while SEPARATOR in name:
        name = name.replace(SEPARATOR, "")
    return name

def get_flattened_path(rel_path):

    p = Path(rel_path)
    parts = p.parts
    
    # 对路径的每一部分进行净化
    sanitized_parts = [sanitize_name(p) for p in parts]
    
    if len(sanitized_parts) <= 1:
        return sanitized_parts[0]
    
    # 提取第一级目录
    top_folder = sanitized_parts[0]
    
    if len(sanitized_parts) > 1:
        # 剩下的部分用 SEPARATOR 连接
        rest_of_path = sanitized_parts[1:]
        new_filename = SEPARATOR.join(rest_of_path)
        return f"{top_folder}/{new_filename}"
        
    return rel_path

def generate_directory_structure(root_dir, sources, ignore_list=None):
    if ignore_list is None:
        ignore_list = []
    
    result = {
        "dirs": [],
        "files": []
    }
    
    for current_dir, subdirs, files in os.walk(root_dir):
        rel_dir = os.path.relpath(current_dir, root_dir)
        if rel_dir == ".":
            rel_dir = ""
        
        subdirs[:] = [d for d in subdirs if d not in ignore_list]
        files = [f for f in files if f not in ignore_list]
        
        if rel_dir == "":
            for file in files:
                if not any(ignore in file for ignore in ignore_list):
                    entry = create_file_entry(file, file, root_dir, sources)
                    result["files"].append(entry)
        else:
            dir_name = os.path.basename(current_dir)
            if dir_name in ignore_list:
                continue
                
            dir_entry = {
                "name": dir_name,
                "path": rel_dir.replace("\\", "/"),
                "files": []
            }
            
            for file in files:
                if file in ignore_list:
                    continue
                    
                file_rel_path = os.path.join(rel_dir, file).replace("\\", "/")
                entry = create_file_entry(file, file_rel_path, root_dir, sources)
                dir_entry["files"].append(entry)
            
            result["dirs"].append(dir_entry)
    
    return result

def create_file_entry(name, rel_path, root_dir, sources):
    full_path = os.path.join(root_dir, rel_path)
    size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
    standard_rel_path = rel_path.replace("\\", "/")
    
    entry = {
        "name": name,
        "path": standard_rel_path,
        "size": size
    }

    for source in sources:
        if not source["enabled"]: continue
        
        if source.get("type") == "flat":
            # 扁平化源 -> 使用净化后的路径
            final_path = get_flattened_path(standard_rel_path)
        else:
            # 树状源 -> 使用原始路径 (GitHub/R2 支持空格和特殊字符)
            final_path = standard_rel_path
            
        encoded_path = quote(final_path)
        url = f"{source['base'].rstrip('/')}/{encoded_path}"
        entry[source["key"]] = url
            
    return entry

def load_ignore_list(root_dir, ignore_file=".gitignore"):
    ignore_list = set(DEFAULT_IGNORES)
    ignore_path = os.path.join(root_dir, ignore_file)
    if os.path.exists(ignore_path):
        try:
            with open(ignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        ignore_list.add(line)
        except Exception:
            pass
    return list(ignore_list)

if __name__ == "__main__":
    TARGET_DIR = DEFAULT_TARGET_DIR
    OUTPUT_FILE = "directory_structure.json"
    
    if len(sys.argv) > 1:
        TARGET_DIR = sys.argv[1]
    
    if not os.path.isdir(TARGET_DIR):
        print(f"错误: 目录 '{TARGET_DIR}' 不存在")
        sys.exit(1)
        
    IGNORE_LIST = load_ignore_list(TARGET_DIR)
    print(f"正在扫描: {TARGET_DIR}")
    
    structure = generate_directory_structure(TARGET_DIR, SOURCES, IGNORE_LIST)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    
    print("-" * 30)
    print(f"JSON 已生成: {OUTPUT_FILE}")
    if structure['files']:
        print("根文件示例:\n", json.dumps(structure['files'][0], indent=2, ensure_ascii=False))
