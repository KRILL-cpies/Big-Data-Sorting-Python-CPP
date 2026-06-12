import os
import heapq
import sys
import time
import shutil
import csv
MAX_MEMORY_MB = 80 
ESTIMATED_ROW_SIZE = 120 
ROWS_PER_CHUNK = (MAX_MEMORY_MB * 1024 * 1024) // ESTIMATED_ROW_SIZE

TEMP_DIR = "temp_chunks_py"
HEADER = ["Name","Company","ReleaseDate","Genre","Coop","Playtime","Rating"]

COL_MAP = {"name": 0, "company": 1, "date": 2, "genre": 3, "coop": 4, "playtime": 5, "rating": 6}

def get_key(row, key_name, col_idx):
    val = row[col_idx]
    if key_name == 'playtime': return float(val)
    if key_name == 'rating': return int(val)
    return val

def split_file(input_file, key_name):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    chunk_files = []
    col_idx = COL_MAP.get(key_name, 0)    
    with open(input_file, 'r', encoding='utf-8', newline='', buffering=1024*1024) as f:
        reader = csv.reader(f)
        next(reader) 
        
        buffer = []
        chunk_id = 0
        
        for row in reader:
            k = get_key(row, key_name, col_idx)
            buffer.append((k, row))
            
            if len(buffer) >= ROWS_PER_CHUNK:
                buffer.sort(key=lambda x: x[0])
                
                chunk_path = os.path.join(TEMP_DIR, f"chunk_{chunk_id}.csv")
                with open(chunk_path, 'w', encoding='utf-8', newline='', buffering=1024*1024) as cf:
                    writer = csv.writer(cf)
                    for _, r in buffer:
                        writer.writerow(r)
                
                chunk_files.append(chunk_path)
                buffer = []
                chunk_id += 1
        
        if buffer:
            buffer.sort(key=lambda x: x[0])
            chunk_path = os.path.join(TEMP_DIR, f"chunk_{chunk_id}.csv")
            with open(chunk_path, 'w', encoding='utf-8', newline='', buffering=1024*1024) as cf:
                writer = csv.writer(cf)
                for _, r in buffer:
                    writer.writerow(r)
            chunk_files.append(chunk_path)

    return chunk_files

def merge_files(chunk_files, output_file, key_name):
    col_idx = COL_MAP.get(key_name, 0)
    def read_chunk(path):
        with open(path, 'r', encoding='utf-8', newline='', buffering=1024*1024) as f:
            reader = csv.reader(f)
            for row in reader:
                k = get_key(row, key_name, col_idx)
                yield (k, row)

    file_iters = [read_chunk(f) for f in chunk_files]
    
    with open(output_file, 'w', encoding='utf-8', newline='', buffering=1024*1024) as out_f:
        writer = csv.writer(out_f)
        writer.writerow(HEADER)
        for k, row in heapq.merge(*file_iters, key=lambda x: x[0]):
            writer.writerow(row)

    shutil.rmtree(TEMP_DIR)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(1)
    input_file, output_file, key_choice = sys.argv[1], sys.argv[2], sys.argv[3].lower()
    if key_choice not in COL_MAP:
        sys.exit(1)
    
    try:
        t1 = time.time()
        chunks = split_file(input_file, key_choice)
        t2 = time.time()
        merge_files(chunks, output_file, key_choice)
        t3 = time.time()
        print(f"[Python] Split: {t2-t1:.2f}s, Merge: {t3-t2:.2f}s, Total: {t3-t1:.2f}s")
    except Exception as e:
        print(f"[Python] Error: {e}")
        sys.exit(1)
