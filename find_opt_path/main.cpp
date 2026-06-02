#include "QuadTree.h"
#include "Obstacle.h"
#include "ConfigParser.h"
#include <iostream>
#include <queue>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>

// ---------- Состояние для BFS ----------
struct State {
    int x, y, time;
    State(int x = 0, int y = 0, int t = 0) : x(x), y(y), time(t) {}
    bool operator==(const State& other) const {
        return x == other.x && y == other.y && time == other.time;
    }
};

namespace std {
    template<> struct hash<State> {
        size_t operator()(const State& s) const {
            return ((hash<int>()(s.x) ^ (hash<int>()(s.y) << 1)) ^ (hash<int>()(s.time) << 2));
        }
    };
}

//Поиск пути 
std::vector<State> findPath(const QuadTree& maze, int size,
    const Point& start, const Point& exit,
    const Obstacle& obstacle, int maxTime = 500) {
    std::queue<State> q;
    std::unordered_set<State> visited;
    std::unordered_map<State, State> parent;

    State init(start.x, start.y, 0);
    q.push(init);
    visited.insert(init);

    const int dx[] = { 0, 0, -1, 1, 0 }; // 4 направления + ожидание
    const int dy[] = { -1, 1, 0, 0, 0 };

    while (!q.empty()) {
        State cur = q.front(); q.pop();

        if (cur.x == exit.x && cur.y == exit.y) {
            std::vector<State> path;
            State s = cur;
            while (!(s.x == start.x && s.y == start.y && s.time == 0)) {
                path.push_back(s);
                s = parent[s];
            }
            path.push_back(init);
            std::reverse(path.begin(), path.end());
            return path;
        }

        if (cur.time >= maxTime) continue;

        for (int dir = 0; dir < 5; ++dir) {
            int nx = cur.x + dx[dir];
            int ny = cur.y + dy[dir];
            int nt = cur.time + 1;
            if (nx < 0 || nx >= size || ny < 0 || ny >= size) continue;
            if (maze.isWall(nx, ny)) continue;

            auto occupied = obstacle.getOccupiedCells(nt);
            bool blocked = false;
            for (const Point& cell : occupied) {
                if (nx == cell.x && ny == cell.y) {
                    blocked = true;
                    break;
                }
            }
            if (blocked) continue;

            State next(nx, ny, nt);
            if (!visited.count(next)) {
                visited.insert(next);
                parent[next] = cur;
                q.push(next);
            }
        }
    }
    return {};
}

// Функция для генерации JSON строки
std::string escape_json(const std::string& s) {
    std::string out;
    for (char c : s) {
        switch (c) {
        case '"': out += "\\\""; break;
        case '\\': out += "\\\\"; break;
        case '\b': out += "\\b"; break;
        case '\f': out += "\\f"; break;
        case '\n': out += "\\n"; break;
        case '\r': out += "\\r"; break;
        case '\t': out += "\\t"; break;
        default: out += c; break;
        }
    }
    return out;
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <config_file.txt>" << std::endl;
        return 1;
    }
    std::string filename = argv[1];

    MazeConfig config;
    if (!loadMazeConfig(filename, config)) {
        std::cerr << "Error loading configuration." << std::endl;
        return 1;
    }

    QuadTree maze(config.size, config.walls);
    Obstacle obstacle(config.obstacleShape, config.obstacleRoute,
        config.obstacleMode, config.obstacleSpeed);

    Point start(config.startX, config.startY);
    Point exit(config.exitX, config.exitY);

    
    if (maze.isWall(start.x, start.y) || maze.isWall(exit.x, exit.y)) {
        std::cerr << "Start or exit is a wall!" << std::endl;
        return 1;
    }

    auto path = findPath(maze, config.size, start, exit, obstacle, 500);


    // Начинаем вывод JSON
    std::cout << "{\n";
    std::cout << "  \"path\": [\n";
    if (!path.empty()) {
        for (size_t i = 0; i < path.size(); ++i) {
            std::cout << "    {\"x\":" << path[i].x << ",\"y\":" << path[i].y << ",\"t\":" << path[i].time << "}";
            if (i != path.size() - 1) std::cout << ",";
            std::cout << "\n";
        }
    }
    std::cout << "  ],\n";

    // Вычисляем позиции препятствия для каждого момента времени от 0 до времени выхода
    std::cout << "  \"obstacle_positions\": [\n";
    if (!path.empty()) {
        int exit_time = path.back().time;
        for (int t = 0; t <= exit_time; ++t) {
            auto cells = obstacle.getOccupiedCells(t);
            std::cout << "    {\"t\":" << t << ",\"cells\":[";
            for (size_t i = 0; i < cells.size(); ++i) {
                std::cout << "[" << cells[i].x << "," << cells[i].y << "]";
                if (i != cells.size() - 1) std::cout << ",";
            }
            std::cout << "]}";
            if (t != exit_time) std::cout << ",";
            std::cout << "\n";
        }
    }
    std::cout << "  ]\n";
    std::cout << "}\n";

    return 0;
}