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
    config.obstacleMode = 1;   // cyclic по умолчанию
    config.obstacleSpeed = 1;
    config.size = 0;

    std::string token;
    while (file >> token) {
        if (token == "size") {
            file >> config.size;
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
            // Пропускаем пробелы и читаем первую строку маршрута
            file >> std::ws;
            // Читаем всю строку целиком (остаток текущей строки)
            std::string line;
            std::getline(file, line);
            std::istringstream lineStream(line);
            int x, y;
            while (lineStream >> x >> y) {
                config.obstacleRoute.push_back(Point(x, y));
            }
        }
        else if (token == "mode") {
            std::string modeStr;
            file >> modeStr;
            if (modeStr == "once") config.obstacleMode = 0;
            else if (modeStr == "cyclic") config.obstacleMode = 1;
            else if (modeStr == "back_and_forth") config.obstacleMode = 2;
            else config.obstacleMode = 1;
        }
        else if (token == "speed") {
            file >> config.obstacleSpeed;
        }
    }

    if (config.size == 0 || config.walls.empty()) {
        std::cerr << "Ошибка: не задан размер или стены лабиринта" << std::endl;
        return false;
    }
    return true;
}