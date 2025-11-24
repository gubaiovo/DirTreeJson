import os
import json
import sys
from urllib.parse import quote

# 目标目录
DEFAULT_TARGET_DIR = "/mnt/c/Users/asus/Documents/GitHub/JNU-EXAM"

SOURCES = [
    {
        "name": "Github",           # 显示在 source_list 中的名称
        "key": "github_raw_url",    # JSON 中每个文件对应的键名
        "base": "https://github.com/gubaiovo/JNU-EXAM/raw/main", # URL 前缀
        "enabled": True             # 是否启用
    },
    {
        "name": "Gitee",
        "key": "gitee_raw_url",
        "base": "https://gitee.com/gubaiovo/jnu-exam/raw/main",
        "enabled": True
    },
    {
        "name": "CloudFlare R2",
        "key": "cf_url",
        "base": "https://jnuexam.xyz", 
        "enabled": True
    }
]

# 忽略列表
DEFAULT_IGNORES = [
    ".git", ".gitignore", "upload.txt", "directory_structure.json", 
    ".idea", ".vscode", "__pycache__"
]


def generate_directory_structure(root_dir, sources, ignore_list=None):
    if ignore_list is None:
        ignore_list = []
    
    # 1. 生成根节点的 source_list (只包含已启用的源名称)
    active_source_names = [s["name"] for s in sources if s["enabled"]]

    result = {
        "source_list": active_source_names,
        "dirs": [],
        "files": []
    }
    
    for current_dir, subdirs, files in os.walk(root_dir):
        rel_dir = os.path.relpath(current_dir, root_dir)
        if rel_dir == ".":
            rel_dir = ""
        
        # 过滤目录
        subdirs[:] = [d for d in subdirs if d not in ignore_list]
        
        # 过滤文件
        files = [f for f in files if f not in ignore_list]
        
        # 根目录下的文件
        if rel_dir == "":
            for file in files:
                if not any(ignore in file for ignore in ignore_list):
                    entry = create_file_entry(file, file, root_dir, sources)
                    result["files"].append(entry)
                    
        # 子目录
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
    clean_path = rel_path.replace("\\", "/")
    
    # URL 编码
    encoded_path = quote(clean_path)
    
    # 基础信息
    entry = {
        "name": name,
        "path": clean_path,
        "size": size
    }

    for source in sources:
        if source["enabled"]:
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
    OUTPUT_FILE = "directory_structuretest.json"
    
    if len(sys.argv) > 1:
        TARGET_DIR = sys.argv[1]
    
    if not os.path.isdir(TARGET_DIR):
        print(f"错误: 目录 '{TARGET_DIR}' 不存在")
        sys.exit(1)
        
    IGNORE_LIST = load_ignore_list(TARGET_DIR)
    print(f"正在扫描: {TARGET_DIR}")
    
    # 生成结构
    structure = generate_directory_structure(TARGET_DIR, SOURCES, IGNORE_LIST)
    
    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    
    print("-" * 30)
    print(f"成功! JSON 已生成: {OUTPUT_FILE}")
    print(f"当前源列表: {structure['source_list']}")
    
    if structure['files']:
        print("根文件示例:\n", json.dumps(structure['files'][0], indent=2, ensure_ascii=False))
