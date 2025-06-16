import os
import json
import sys

def generate_directory_structure(root_dir, github_repo, gitee_repo, ignore_list=None):
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
                file_path = os.path.join(current_dir, file)
                if not any(ignore in file for ignore in ignore_list):
                    result["files"].append(create_file_entry(file, file, root_dir, github_repo, gitee_repo))
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
                dir_entry["files"].append(create_file_entry(file, file_rel_path, root_dir, github_repo, gitee_repo))
            
            result["dirs"].append(dir_entry)
    
    return result

def create_file_entry(name, rel_path, root_dir, github_repo, gitee_repo):
    full_path = os.path.join(root_dir, rel_path)
    size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
    
    return {
        "name": name,
        "path": rel_path.replace("\\", "/"),
        "size": size,
        "github_raw_url": f"{github_repo}/raw/main/{rel_path.replace('\\', '/')}",
        "gitee_raw_url": f"{gitee_repo}/raw/main/{rel_path.replace('\\', '/')}"
    }

def load_ignore_list(ignore_file=".ignorelist"):
    if os.path.exists(ignore_file):
        with open(ignore_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
    return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TARGET_DIR = sys.argv[1]
    else:
        TARGET_DIR = input("请输入要扫描的目录路径: ").strip()
    
    OUTPUT_FILE = "directory_structure.json"
    GITHUB_REPO = "https://github.com/gubaiovo/JNU-EXAM"
    GITEE_REPO = "https://gitee.com/gubaiovo/jnu-exam"
    
    IGNORE_LIST = load_ignore_list()
    if IGNORE_LIST:
        print(f"使用忽略名单: {IGNORE_LIST}")
    
    if not os.path.isdir(TARGET_DIR):
        print(f"错误: 目录 '{TARGET_DIR}' 不存在")
        sys.exit(1)
    
    structure = generate_directory_structure(TARGET_DIR, GITHUB_REPO, GITEE_REPO, IGNORE_LIST)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    
    print(f"目录结构已成功导出到 {OUTPUT_FILE}")
