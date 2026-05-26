#ifndef OBSTACLE_H
#define OBSTACLE_H

#include <vector>
#include "Point.h"

class Obstacle {
public:
    Obstacle(const std::vector<Point>& shape,
        const std::vector<Point>& route,
        int mode, int speed);
    std::vector<Point> getOccupiedCells(int time) const;

private:
    std::vector<Point> shape_;
    std::vector<Point> route_;
    int mode_;
    int speed_;
    int getWaypointIndex(int step) const;
};

#endif // OBSTACLE_H