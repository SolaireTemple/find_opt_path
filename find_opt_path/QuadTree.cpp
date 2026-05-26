#include "QuadTree.h"

QuadTree::Node::Node(int x, int y, int w, int h, bool wall): x(x), y(y), w(w), h(h), isWall(wall), leaf(true) {}

QuadTree::QuadTree(int size, const std::vector<std::vector<bool>>& walls): size_(size) {root_ = build(0, 0, size, walls);}

std::unique_ptr<QuadTree::Node> QuadTree::build(int x, int y, int w, const std::vector<std::vector<bool>>& walls) {

    bool uniform = true;
    bool first = walls[y][x];
    for (int i = y; i < y + w && uniform; ++i)
        for (int j = x; j < x + w && uniform; ++j)
            if (walls[i][j] != first) {
                uniform = false;
            }

    if (uniform || w == 1) {
        return std::make_unique<Node>(x, y, w, w, first);
    }

    auto node = std::make_unique<Node>(x, y, w, w, false);
    node->leaf = false;
    int half = w / 2;
    node->children[0] = build(x, y, half, walls);
    node->children[1] = build(x + half, y, half, walls);
    node->children[2] = build(x, y + half, half, walls);
    node->children[3] = build(x + half, y + half, half, walls);
    return node;
}

bool QuadTree::isWall(int x, int y) const {
    if (x < 0 || x >= size_ || y < 0 || y >= size_) return true;
    return isWall(root_.get(), x, y);
}

bool QuadTree::isWall(const Node* node, int x, int y) const {
    if (node->leaf) return node->isWall;
    int midX = node->x + node->w / 2;
    int midY = node->y + node->h / 2;
    int idx = 0;
    if (x >= midX) idx |= 1;
    if (y >= midY) idx |= 2;
    static const int map[4] = { 0,1,2,3 };
    return isWall(node->children[map[idx]].get(), x, y);
}