STEPS = [(1, 0), (0, 1), (-1, 0), (0, -1)]

def print_matrix(matrix):
    for row in matrix:
        print("\t".join(f"{num:6.0f}" for num in row))
    print("------------------")

def read_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    n, m = map(int, lines[0].split())
    matrix = [[float(num) for num in line.split()] for line in lines[1:n + 1]]
    return matrix

def get_n_wave(M, n):
    for m in range(n):
        for i in range(len(M)):
            for j in range(len(M[i])):
                if M[i][j] == m:
                    for dx, dy in STEPS:
                        x, y = i + dx, j + dy
                        if 0 <= x < len(M) and 0 <= y < len(M[i]) and M[x][y] == -1:
                            M[x][y] = m + 1

def intersect(matrices):
    result = [[-1] * len(matrices[0][0]) for _ in range(len(matrices[0]))]

    for i in range(len(matrices[0])):
        for j in range(len(matrices[0][i])):
            intersect_value = matrices[0][i][j]
            for matrix in matrices[1:]:
                if intersect_value == -2 or matrix[i][j] == -2:
                    intersect_value = -2
                elif intersect_value >= 0 and matrix[i][j] >= 0:
                    intersect_value = 0
                elif intersect_value == -1 or matrix[i][j] == -1:
                    intersect_value = -1
            result[i][j] = intersect_value
    return result


def main():
    N = 3
    p = 7
    tau = 2
    matrices1 = [read_file(f"file{i}.txt") for i in range(N)]
    for i in range(N):
        get_n_wave(matrices1[i], p - tau)
        print_matrix(matrices1[i])

    W0 = intersect(matrices1)
    print_matrix(W0)
    get_n_wave(W0, tau)
    print_matrix(W0)


if __name__ == "__main__":
    main()