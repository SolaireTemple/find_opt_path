#ifndef CONFIGPARSER_H
#define CONFIGPARSER_H

#include <vector>
#include <string>
#include "Point.h"

struct MazeConfig {
    int size;
    std::vector<std::vector<bool>> walls;
    std::vector<Point> obstacleShape;
    std::vector<Point> obstacleRoute;
    int obstacleMode;      // 0,1,2
    int obstacleSpeed;
    int startX, startY;    // новые поля
    int exitX, exitY;      // новые поля
};

bool loadMazeConfig(const std::string& filename, MazeConfig& config);

#endif