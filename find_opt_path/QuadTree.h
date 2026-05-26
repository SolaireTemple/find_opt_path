#ifndef QUADTREE_H
#define QUADTREE_H

#include <vector>
#include <memory>
#include "Point.h"

class QuadTree {
public:
    QuadTree(int size, const std::vector<std::vector<bool>>& walls);
    ~QuadTree() = default;
    bool isWall(int x, int y) const;

private:
    struct Node {
        int x, y, w, h;
        bool isWall;
        bool leaf;
        std::unique_ptr<Node> children[4];
        Node(int x, int y, int w, int h, bool wall);
    };
    std::unique_ptr<Node> root_;
    int size_;
    std::unique_ptr<Node> build(int x, int y, int w, const std::vector<std::vector<bool>>& walls);
    bool isWall(const Node* node, int x, int y) const;
};

#endif // QUADTREE_H