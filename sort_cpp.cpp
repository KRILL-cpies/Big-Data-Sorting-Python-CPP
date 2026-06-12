#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <algorithm>
#include <queue>
#include <filesystem>
#include <chrono>

namespace fs = std::filesystem;

const size_t MAX_MEM_MB = 100;
const size_t EST_ROW_SIZE = 120;
const size_t ROWS_PER_CHUNK = (MAX_MEM_MB * 1024 * 1024) / EST_ROW_SIZE;
const std::string TEMP_DIR = "temp_chunks_cpp";

std::string keyMode = "rating";
struct ParsedKey {
    int type; // 0:string, 1:double, 2:int
    std::string sVal;
    double dVal;
    int iVal;

    bool operator<(const ParsedKey& other) const {
        if (type != other.type) return type < other.type;
        if (type == 0) return sVal < other.sVal;
        if (type == 1) return dVal < other.dVal;
        return iVal < other.iVal;
    }
};

ParsedKey extractKey(const std::string& line, const std::string& mode) {
    ParsedKey pk;
    size_t start = 0, end = 0;
    int col = 0;
    int targetCol = 0;
    if (mode == "name") targetCol = 0;
    else if (mode == "company") targetCol = 1;
    else if (mode == "date") targetCol = 2;
    else if (mode == "genre") targetCol = 3;
    else if (mode == "coop") targetCol = 4;
    else if (mode == "playtime") { targetCol = 5; pk.type = 1; }
    else if (mode == "rating") { targetCol = 6; pk.type = 2; }
    else { pk.type = 0; } // default

    for (int i = 0; i <= targetCol; ++i) {
        end = line.find(',', start);
        if (end == std::string::npos) end = line.length();
        if (i == targetCol) {
            std::string val = line.substr(start, end - start);
            if (pk.type == 1) pk.dVal = std::stod(val);
            else if (pk.type == 2) pk.iVal = std::stoi(val);
            else { pk.type = 0; pk.sVal = val; }
            break;
        }
        start = end + 1;
    }
    return pk;
}

struct Record {
    ParsedKey key;
    std::string line;
    
    bool operator>(const Record& other) const {
        return key < other.key;
    }
    // Äëÿ std::sort
    bool operator<(const Record& other) const {
        return key < other.key;
    }
};

void splitFile(const std::string& inputPath) {
    auto start = std::chrono::high_resolution_clock::now();
    fs::create_directories(TEMP_DIR);
    
    std::ifstream inFile(inputPath);
    std::string line;
    std::getline(inFile, line);

    std::vector<Record> buffer;
    buffer.reserve(ROWS_PER_CHUNK);
    int chunkId = 0;

    while (std::getline(inFile, line)) {
        if (line.empty()) continue;
        Record r;
        r.line = line;
        r.key = extractKey(line, keyMode);
        buffer.push_back(r);

        if (buffer.size() >= ROWS_PER_CHUNK) {
            std::sort(buffer.begin(), buffer.end());
            std::string fName = TEMP_DIR + "/chunk_" + std::to_string(chunkId) + ".csv";
            std::ofstream out(fName, std::ios::binary);
            for (const auto& r : buffer) out << r.line << "\n";
            out.close();
            buffer.clear();
            chunkId++;
        }
    }
    if (!buffer.empty()) {
        std::sort(buffer.begin(), buffer.end());
        std::string fName = TEMP_DIR + "/chunk_" + std::to_string(chunkId) + ".csv";
        std::ofstream out(fName, std::ios::binary);
        for (const auto& r : buffer) out << r.line << "\n";
        out.close();
    }
    inFile.close();

    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "[C++] Split done. Chunks: " << chunkId 
              << " Time: " << std::chrono::duration<double>(end - start).count() << "s" << std::endl;
}

struct HeapItem {
    Record record;
    int fileIdx;
    std::ifstream* stream;
    bool operator>(const HeapItem& other) const {
        return other.record.key < record.key; 
    }
};

void mergeFiles(const std::string& outputPath) {
    auto start = std::chrono::high_resolution_clock::now();
    std::priority_queue<HeapItem, std::vector<HeapItem>, std::greater<HeapItem>> pq;
    std::vector<std::ifstream*> streams;

    for (const auto& entry : fs::directory_iterator(TEMP_DIR)) {
        if (entry.path().extension() == ".csv") {
            std::ifstream* fs = new std::ifstream(entry.path(), std::ios::binary);
            streams.push_back(fs);
            std::string line;
            if (std::getline(*fs, line)) {
                HeapItem item;
                item.record.line = line;
                item.record.key = extractKey(line, keyMode);
                item.fileIdx = streams.size() - 1;
                item.stream = fs;
                pq.push(item);
            }
        }
    }

    std::ofstream out(outputPath, std::ios::binary);
    out << "Name,Company,ReleaseDate,Genre,Coop,Playtime,Rating\n";

    while (!pq.empty()) {
        HeapItem top = pq.top();
        pq.pop();
        out << top.record.line << "\n";

        std::string line;
        if (std::getline(*top.stream, line)) {
            top.record.line = line;
            top.record.key = extractKey(line, keyMode);
            pq.push(top);
        } else {
            top.stream->close();
            delete top.stream;
        }
    }
    out.close();
    for (auto s : streams) { if(s->is_open()) { s->close(); delete s; } }
    fs::remove_all(TEMP_DIR);

    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "[C++] Merge done. Time: " << std::chrono::duration<double>(end - start).count() << "s" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 4) return 1;
    keyMode = argv[3];
    splitFile(argv[1]);
    mergeFiles(argv[2]);
    std::cout << "[C++] Total Success." << std::endl;
    return 0;
}