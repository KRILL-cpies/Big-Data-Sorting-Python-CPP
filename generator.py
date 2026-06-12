import random
import os
import sys

DEFAULT_SIZE_GB = 1.1
OUTPUT_FILE = "data.csv"
CHUNK_ROWS = 50000 

ADJECTIVES = [
    "Epic", "Super", "Mega", "Hyper", "Cyber", "Neo", "Retro", "Dark", "Holy", 
    "Silent", "Bloody", "Crystal", "Iron", "Golden", "Shadow", "Star", "Space", 
    "Wild", "Crazy", "Magic", "Mystic", "Ancient", "Future", "Lost", "Hidden",
    "Ultimate", "Extreme", "Deadly", "Infinite", "Quantum", "Pixel", "Voxel"
]

NOUNS = [
    "Quest", "War", "Warrior", "Legend", "Simulator", "Tycoon", "Empire", 
    "Kingdom", "Adventure", "Survival", "Racing", "Fighter", "Puzzle", 
    "Dungeon", "Tower", "Defense", "Strike", "Ops", "Craft", "World", 
    "Planet", "Galaxy", "Zone", "Frontier", "Horizon", "Chronicles", "Saga"
]

SUFFIXES = [
    "", "2", "3", "Remastered", "Edition", "Online", "Reborn", "Origins", 
    "Unleashed", "Evolution", "Zero", "X", "HD", "Mobile", "VR"
]

COMPANIES = [
    "SoftGiant", "IndieDev", "GameStudio", "PixelArt", "CodeMasters", 
    "VirtualWorlds", "NeonWorks", "BlueOcean", "RedSquare", "GreenLeaf",
    "IronHorse", "StarDust", "MoonLight", "SunRay", "DeepSpace", "HyperLoop"
]

GENRES = ["RPG", "Action", "Strategy", "Simulation", "Puzzle", "Shooter", "Adventure", "Horror", "Sport", "Platformer"]
COOP_OPTIONS = ["Yes", "No"]

def generate_name():
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    suffix = random.choice(SUFFIXES)
    if random.random() > 0.8:
        return f"{adj} {noun}: {random.choice(NOUNS)} {suffix}".strip()
    return f"{adj} {noun} {suffix}".strip()

def generate_date():
    year = random.randint(1995, 2024)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"

def main():
    try:
        target_gb = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SIZE_GB
    except ValueError:
        target_gb = DEFAULT_SIZE_GB

    print(f"Начало генерации (Цель: {target_gb} ГБ)...")
    
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    target_bytes = target_gb * 1024 * 1024 * 1024
    total_rows = 0
    
    header = "Name,Company,ReleaseDate,Genre,Coop,Playtime,Rating\n"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline='') as f:
        f.write(header)
    
    current_size = os.path.getsize(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "a", encoding="utf-8", newline='') as f:
        buffer = []
        
        while current_size < target_bytes:
            for _ in range(CHUNK_ROWS):
                name = generate_name()
                company = random.choice(COMPANIES)
                date = generate_date()
                genre = random.choice(GENRES)
                coop = random.choice(COOP_OPTIONS)
                
                playtime = random.uniform(0.5, 500.0)
                if random.random() > 0.3:
                    rating = random.randint(70, 99)
                else:
                    rating = random.randint(0, 69)
                
                row = f"{name},{company},{date},{genre},{coop},{playtime:.2f},{rating}\n"
                buffer.append(row)
                total_rows += 1
            
            f.writelines(buffer)
            f.flush()
            
            current_size = os.path.getsize(OUTPUT_FILE)
            buffer = []
            
            if total_rows % 1000000 == 0:
                print(f"Строк: {total_rows}, Размер: {current_size / 1024 / 1024:.1f} МБ")

    size_gb = current_size / 1024 / 1024 / 1024
    print(f"Генерация завершена. Строк: {total_rows}, Размер: {size_gb:.2f} ГБ")

if __name__ == "__main__":
    main()
