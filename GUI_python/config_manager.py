import tempfile
import os

# ---------- Генерация конфигурационного файла ----------
def generate_config_file(maze_editor, obstacle_editor):
    """Создаёт временный конфигурационный файл и возвращает его путь."""
    size = maze_editor.size
    walls = maze_editor.get_walls_matrix()
    start_x, start_y = maze_editor.get_start()
    exit_x, exit_y = maze_editor.get_exit()
    shape = obstacle_editor.get_shape()
    route = obstacle_editor.get_route()
    mode_str = obstacle_editor.get_mode()
    speed = obstacle_editor.get_speed()

    if not shape:
        shape = [(0, 0)]
    if not route:
        route = [(0, 0)]

    # Преобразуем режим движения в число
    mode_map = {"once": 0, "cyclic": 1, "back_and_forth": 2}
    mode = mode_map.get(mode_str, 1)

    max_dx = max(dx for dx, _ in shape)
    max_dy = max(dy for _, dy in shape)
    width = max_dx + 1
    height = max_dy + 1

    fd, path = tempfile.mkstemp(suffix=".txt", text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(f"size {size}\n")
        f.write(f"start {start_x} {start_y}\n")
        f.write(f"exit {exit_x} {exit_y}\n")
        f.write("walls\n")
        for row in walls:
            f.write(" ".join(str(cell) for cell in row) + "\n")
        f.write("obstacle_shape\n")
        f.write(f"{width} {height}\n")
        for dx, dy in shape:
            f.write(f"{dx} {dy}\n")
        f.write("obstacle_route\n")
        for x, y in route:
            f.write(f"{x} {y}\n")
        f.write(f"mode {mode}\n")
        f.write(f"speed {speed}\n")
    return path

def delete_config_file(path):
    if path and os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass

# ---------- Загрузка конфигурационного файла ----------
def load_config_file(filename, maze_editor, obstacle_editor):
    """Загружает конфигурацию из текстового файла и обновляет редакторы"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    idx = 0
    size = maze_editor.size
    walls = None
    start = (0, 0)
    exit_ = (size - 1, size - 1)
    shape = None
    route = None
    mode = "cyclic"
    speed = 1

    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        parts = line.split()
        keyword = parts[0]

        match keyword:
            case "size":
                size = int(parts[1])
                idx += 1
            case "start":
                start = (int(parts[1]), int(parts[2]))
                idx += 1
            case "exit":
                exit_ = (int(parts[1]), int(parts[2]))
                idx += 1
            case "walls":
                walls = []
                idx += 1
                for i in range(size):
                    row = list(map(int, lines[idx].split()))
                    walls.append(row)
                    idx += 1
            case "obstacle_shape":
                idx += 1
                w, h = map(int, lines[idx].split())
                idx += 1
                shape_cells = []
                for _ in range(h):
                    for __ in range(w):
                        ox, oy = map(int, lines[idx].split())
                        shape_cells.append((ox, oy))
                        idx += 1
                shape = shape_cells
            case "obstacle_route":
                route_points = []
                idx += 1
                while idx < len(lines):
                    line2 = lines[idx].strip()
                    if not line2:
                        idx += 1
                        continue
                    if line2.startswith(('mode', 'speed', 'size', 'start', 'exit', 'walls', 'obstacle_shape')):
                        break
                    parts2 = line2.split()
                    if len(parts2) >= 2:
                        x, y = int(parts2[0]), int(parts2[1])
                        route_points.append((x, y))
                    idx += 1
                route = route_points
                continue
            case "mode":
                mode_val = parts[1]
                if mode_val.isdigit():
                    mode_int = int(mode_val)
                    if mode_int == 0:
                        mode = "once"
                    elif mode_int == 1:
                        mode = "cyclic"
                    elif mode_int == 2:
                        mode = "back_and_forth"
                    else:
                        mode = "cyclic"
                else:
                    mode = mode_val
                idx += 1
            case "speed":
                speed = int(parts[1])
                idx += 1
            case _:
                idx += 1

    # Применяем загруженные данные к редактору лабиринта
    maze_editor.size = size
    maze_editor.walls = [[walls[y][x] == 1 for x in range(size)] for y in range(size)]
    maze_editor.start = start
    maze_editor.exit = exit_
    maze_editor.update()

    # Синхронизируем лабиринт с редактором препятствия
    obstacle_editor.update_maze_data(maze_editor.get_walls_matrix(), maze_editor.get_start(), maze_editor.get_exit())

    # Применяем данные препятствия
    if shape is not None:
        # Определяем опорную точку: первая точка маршрута или (0,0)
        if route and len(route) > 0:
            base_x, base_y = route[0]
        else:
            base_x, base_y = 0, 0
        absolute_shape = [(base_x + dx, base_y + dy) for dx, dy in shape]
        obstacle_editor.set_shape_cells(absolute_shape)
    if route is not None:
        obstacle_editor.set_route_points(route)
    obstacle_editor.set_mode(mode)
    obstacle_editor.set_speed(speed)
    obstacle_editor.update()