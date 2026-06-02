#include "ConfigParser.h"
#include <fstream>
#include <iostream>
#include <sstream>

bool loadMazeConfig(const std::string& filename, MazeConfig& config) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Не удалось открыть файл: " << filename << std::endl;
        return false;
    }
    // Значения по умолчанию
    config.obstacleMode = 1;   // cyclic
    config.obstacleSpeed = 1;
    config.size = 0;
    config.startX = 0;
    config.startY = 0;
    config.exitX = 0;
    config.exitY = 0;

    std::string token;
    while (file >> token) {
        if (token == "size") {
            file >> config.size;
            if (config.size > 0) {
                config.exitX = config.size - 1;
                config.exitY = config.size - 1;
            }
        }
        else if (token == "walls") {
            if (config.size == 0) {
                std::cerr << "Ошибка: сначала укажите size" << std::endl;
                return false;
            }
            config.walls.assign(config.size, std::vector<bool>(config.size, false));
            for (int i = 0; i < config.size; ++i) {
                for (int j = 0; j < config.size; ++j) {
                    int val;
                    file >> val;
                    config.walls[i][j] = (val == 1);
                }
            }
        }
        else if (token == "obstacle_shape") {
            int w, h;
            file >> w >> h;
            config.obstacleShape.clear();
            for (int dy = 0; dy < h; ++dy) {
                for (int dx = 0; dx < w; ++dx) {
                    int ox, oy;
                    file >> ox >> oy;
                    config.obstacleShape.push_back(Point(ox, oy));
                }
            }
        }
        else if (token == "obstacle_route") {
            config.obstacleRoute.clear();
            int x, y;
            // Читаем все пары чисел, пока они есть
            while (file >> x >> y) {
                config.obstacleRoute.push_back(Point(x, y));
            }
            // Сбрасываем состояние потока, чтобы продолжить чтение остальных секций
            file.clear();
        }
        else if (token == "mode") {
            int modeInt;
            file >> modeInt;
            config.obstacleMode = modeInt;
        }
        else if (token == "speed") {
            file >> config.obstacleSpeed;
        }
        else if (token == "start") {
            file >> config.startX >> config.startY;
        }
        else if (token == "exit") {
            file >> config.exitX >> config.exitY;
        }
    }

    if (config.size == 0 || config.walls.empty()) {
        std::cerr << "Ошибка: не задан размер или стены лабиринта" << std::endl;
        return false;
    }

    
    std::cerr << "=== DEBUG ===" << std::endl;
    std::cerr << "Mode from config: " << config.obstacleMode << std::endl;
    std::cerr << "Route size: " << config.obstacleRoute.size() << std::endl;
    for (auto& p : config.obstacleRoute)
        std::cerr << "  " << p.x << "," << p.y << std::endl;
    std::cerr << "==============" << std::endl;

    return true;
}