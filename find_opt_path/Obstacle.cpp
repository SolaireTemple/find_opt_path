#include "Obstacle.h"
#include <algorithm>

Obstacle::Obstacle(const std::vector<Point>& shape,
    const std::vector<Point>& route,
    int mode, int speed)
    : shape_(shape), route_(route), mode_(mode), speed_(speed) {}

std::vector<Point> Obstacle::getOccupiedCells(int time) const {
    if (route_.empty()) return {};
    int step = time / speed_;
    int idx = getWaypointIndex(step);
    const Point& base = route_[idx];
    std::vector<Point> cells;
    cells.reserve(shape_.size());
    for (const Point& offset : shape_) {
        cells.push_back(Point(base.x + offset.x, base.y + offset.y));
    }
    return cells;
}

int Obstacle::getWaypointIndex(int step) const {
    if (route_.empty()) return 0;
    if (mode_ == 0) { // once
        if (step >= (int)route_.size()) step = (int)route_.size() - 1;
        return step;
    }
    else if (mode_ == 1) { // cyclic
        return step % route_.size();
    }
    else { // back_and_forth
        int period = 2 * ((int)route_.size() - 1);
        if (period <= 0) return 0;
        int t = step % period;
        if (t < (int)route_.size())
            return t;
        else
            return period - t;
    }
}