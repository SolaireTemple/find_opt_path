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

//Поиск пути (волновой BFS с учётом времени и размера препятствия)
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

// ---------- Главная функция ----------
int main() {
    std::string filename;
    std::cout << "Введите имя файла конфигурации: ";
    std::cin >> filename;

    MazeConfig config;
    if (!loadMazeConfig(filename, config)) {
        std::cerr << "Ошибка загрузки конфигурации." << std::endl;
        return 1;
    }

    QuadTree maze(config.size, config.walls);
    Obstacle obstacle(config.obstacleShape, config.obstacleRoute,
        config.obstacleMode, config.obstacleSpeed);

    Point start(0, 0);
    Point exit(config.size - 1, config.size - 1);

    std::cout << "Поиск оптимального пути с учётом движущегося препятствия...\n";
    auto path = findPath(maze, config.size, start, exit, obstacle, 500);

    if (path.empty()) {
        std::cout << "Путь не найден.\n";
    }
    else {
        std::cout << "Путь найден. Время выхода: " << path.back().time << "\n";
        for (const auto& s : path) {
            std::cout << "t=" << s.time << ": (" << s.x << "," << s.y << ")\n";
        }
    }

    return 0;
}