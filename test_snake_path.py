import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString, MultiLineString

def generate_snake_path(polygon, spacing=0.5):
    """
    Генерирует маршрут "змейки" внутри заданного многоугольника.
    """
    path_points = []
    
    # 1. Находим "Bounding Box" (ограничивающую рамку)
    minx, miny, maxx, maxy = polygon.bounds
    
    # Флаг направления (слева направо или справа налево)
    left_to_right = True
    
    # 2. Начинаем "сканировать" снизу вверх с заданным шагом
    current_y = miny
    while current_y <= maxy:
        # Создаем бесконечную линию на текущей высоте
        scan_line = LineString([(minx - 10, current_y), (maxx + 10, current_y)])
        
        # 3. НАХОДИМ ПЕРЕСЕЧЕНИЕ!
        # Спрашиваем Shapely: "Оставь от линии только те куски, которые падают на газон"
        intersection = scan_line.intersection(polygon)
        
        segments = []
        if intersection.is_empty:
            pass # Линия не коснулась газона
        elif intersection.geom_type == 'LineString':
            segments.append(intersection)
        elif intersection.geom_type == 'MultiLineString':
            # Если сложный газон-подкова, линия может разрезаться на несколько кусков
            for geom in intersection.geoms:
                segments.append(geom)

        points = []
        for segment in segments:
            points.extend(list(segment.coords))
            
        # 4. Сортируем точки слева направо или справа налево (чтобы получилась змейка)
        if points:
            # Сортируем все точки на этой линии по оси X (по возрастанию)
            points = sorted(points, key=lambda p: p[0])
            if not left_to_right:
                points.reverse() # Разворачиваем, если едем в обратную сторону
            
            path_points.extend(points)
            # Меняем направление для следующей линии
            left_to_right = not left_to_right
            
        current_y += spacing

    return path_points

def main():
    print("Генерируем газонокосильную магию со сложными углами...")
    
    # Сложный многоугольник (звезда / кривая клякса) ВООБЩЕ БЕЗ ПРЯМЫХ УГЛОВ!
    lawn_coords = [
        (0.0, 0.0),      # Старт снизу
        (8.5, -2.1),     # Вниз вправо
        (13.2, 4.8),     # Уходит направо вверх
        (9.0, 8.5),      # Загибается внутрь
        (11.5, 14.2),    # Торчит вершина вправо-вверх
        (4.0, 16.0),     # Центр верх
        (-2.5, 12.0),    # Уходит влево
        (0.0, 7.5),      # Загибается обратно к центру
        (-5.5, 4.0)      # Острый левый нижний "хвост"
    ]
    lawn_polygon = Polygon(lawn_coords)

    # Шаг между полосами (ширина кошения маленького трактора 0.4 метра)
    snake_path = generate_snake_path(lawn_polygon, spacing=0.4)

    # ===== РИСУЕМ КРАСИВЫЙ ГРАФИК =====
    # Рисуем сам газон (зеленым)
    x, y = lawn_polygon.exterior.xy
    plt.plot(x, y, color='green', linewidth=3, label='Граница газона')
    plt.fill(x, y, alpha=0.2, color='green')

    # Рисуем путь трактора (красным)
    if snake_path:
        path_x = [p[0] for p in snake_path]
        path_y = [p[1] for p in snake_path]
        plt.plot(path_x, path_y, color='red', marker='o', linestyle='-', linewidth=2, label='Путь трактора (Змейка)')

    plt.title("Coverage Path Planning (MVP Алгоритма)")
    plt.xlabel("Meters (X)")
    plt.ylabel("Meters (Y)")
    plt.axis('equal') # Чтобы квадраты были квадратами
    plt.legend()
    plt.grid(True)
    
    print("Готово! Открываю график...")
    plt.show()

if __name__ == '__main__':
    main()
