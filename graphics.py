import pygame
import random
from entities import DroppedItem

def draw_entity(screen, entity, x, y):
    color = (0, 128, 0)  # цвет героя
    pygame.draw.rect(screen, color, pygame.Rect(x, y, 50, 50))  # рисуем героя как квадрат 50x50
    

class DarkBiome:
    def __init__(self, x, y, screen_width, screen_height):
        # Сохраняем размеры экрана
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Задаем размеры темной зоны, она будет занимать 1/4 экрана
        self.width = screen_width // 2  # Ширина = половина ширины экрана
        self.height = screen_height // 2  # Высота = половина высоты экрана
        
        # Размещаем темную зону в правом нижнем углу
        self.x = x + (screen_width // 2)
        self.y = y + (screen_height // 2)

        # Цвет темного биома
        self.color = (0, 0, 0)
        
        # Начальные координаты и размеры для прямоугольника
        self.x_start = self.x
        self.y_start = self.y
        self.x_end = self.x + self.width
        self.y_end = self.y + self.height

    def is_hero_in_biome(self, hero):
        """Проверка, находится ли герой в биоме."""
        return self.x < hero.x < self.x + self.width and self.y < hero.y < self.y + self.height

    def is_rect_in_biome(self, rect):
        """Проверка, находится ли прямоугольник (сегмент гор) в темной зоне."""
        return self.x < rect.right and self.x + self.width > rect.left and self.y < rect.bottom and self.y + self.height > rect.top

    def draw(self, surface, camera_x, camera_y, flashlight=None):
        """Отрисовка темной зоны на экране с учетом смещения камеры."""
        rect_x = self.x_start - camera_x
        rect_y = self.y_start - camera_y
        rect_width = self.x_end - self.x_start
        rect_height = self.y_end - self.y_start
        
        # Отображаем темный биом на экране
        pygame.draw.rect(surface, self.color, pygame.Rect(rect_x, rect_y, rect_width, rect_height))

        # Логика для фонаря (если необходимо)
        if flashlight and flashlight.is_on:
            pass

        
class Flashlight:
    def __init__(self, hero, radius=200):
        self.hero = hero
        self.radius = radius
        self.is_on = False  # Включен ли фонарь

    def draw(self, screen, camera_x, camera_y):
        """Рисуем свет от фонаря на экране."""
        if not self.is_on:
            return  # Если фонарь выключен, не рисуем

        light_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(light_surface, (255, 255, 255, 150), (self.radius, self.radius), self.radius)
        screen.blit(light_surface, (self.hero.x - self.radius - camera_x, self.hero.y - self.radius - camera_y))

    def is_within_light(self, rect):
        """Проверка, попадает ли объект в область света."""
        flashlight_rect = pygame.Rect(self.hero.x - self.radius, self.hero.y - self.radius, self.radius * 2, self.radius * 2)
        return flashlight_rect.colliderect(rect)
    

class Landscape:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.mountains = []  # Список кластеров гор
        self.texture = pygame.image.load("gfx/brown_mountain.png") # Текстуры для гор

    def generate_mountains(self, num_clusters, dark_biome):
        """Генерация кластеров гор, избегая пересечения с темным биомом."""
        for _ in range(num_clusters):
            cluster = []
            start_x = random.randint(0, self.width - 64)
            start_y = random.randint(0, self.height - 64)

            # Создаем начальный блок горы
            queue = [pygame.Rect(start_x, start_y, 64, 64)]
            while queue and len(cluster) < random.randint(10, 30):  # Размер кластера
                block = queue.pop(0)

                # Проверяем пересечение с темным биомом
                if not dark_biome.is_rect_in_biome(block):
                    cluster.append(block)

                    # Добавляем соседние блоки
                    neighbors = [
                        pygame.Rect(block.x + 64, block.y, 64, 64),
                        pygame.Rect(block.x - 64, block.y, 64, 64),
                        pygame.Rect(block.x, block.y + 64, 64, 64),
                        pygame.Rect(block.x, block.y - 64, 64, 64),
                    ]
                    for neighbor in neighbors:
                        if (
                            0 <= neighbor.x < self.width
                            and 0 <= neighbor.y < self.height
                            and neighbor not in queue
                            and neighbor not in cluster
                        ):
                            queue.append(neighbor)

            if cluster:  # Добавляем только непустые кластеры
                self.mountains.append(cluster)

    def draw(self, screen, camera_x, camera_y, flashlight, dark_biome):
        """Отрисовка гор на экране."""
        for cluster in self.mountains:
            for block in cluster:
                screen_x = block.x - camera_x
                screen_y = block.y - camera_y

                # Если в темном биоме, проверяем радиус фонаря
                if dark_biome.is_hero_in_biome(flashlight.hero):
                    if flashlight.is_on and flashlight.is_within_light(block):
                        screen.blit(self.texture, (screen_x, screen_y))  # Отображение текстуры
                else:
                    screen.blit(self.texture, (screen_x, screen_y))  # Отображение текстуры
                    
    def break_block(self, world_x, world_y, gameplay):
        """Разрушение блока, если он существует."""
        for cluster_index, cluster in enumerate(self.mountains):
            for block_index, block in enumerate(cluster):
                if block.collidepoint(world_x, world_y):
                    print(f"Удаляем блок: {block}, кластер: {cluster_index}")
                    cluster.pop(block_index)  # Удаляем блок из кластера

                    # Создаем выпадающий предмет
                    gameplay.dropped_items.append(DroppedItem(block.x + 24, block.y + 24, "brown_mountain_block"))

                    # Удаляем пустые кластеры
                    if not cluster:
                        print(f"Кластер {cluster_index} теперь пуст и будет удалён.")
                        self.mountains.pop(cluster_index)

                    return True  # Блок найден и удалён
        print("Блок не найден.")
        return False
    
class DarkGrayMountains():
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.features = []  # Инициализируем список для хранения кластеров гор
        self.texture = pygame.image.load("gfx/gray_mountain.png")  # Загрузка текстуры

    def generate_features(self, num_clusters, dark_biome):
        """Генерация серых гор, избегая пересечения с темным биомом."""
        for _ in range(num_clusters):
            cluster = []
            start_x = random.randint(0, self.width - 64)
            start_y = random.randint(0, self.height - 64)

            # Создаем начальный блок горы
            queue = [pygame.Rect(start_x, start_y, 64, 64)]
            while queue and len(cluster) < random.randint(10, 30):  # Размер кластера
                block = queue.pop(0)

                # Проверяем пересечение с темным биомом
                if not dark_biome.is_rect_in_biome(block):
                    cluster.append(block)

                    # Добавляем соседние блоки
                    neighbors = [
                        pygame.Rect(block.x + 64, block.y, 64, 64),
                        pygame.Rect(block.x - 64, block.y, 64, 64),
                        pygame.Rect(block.x, block.y + 64, 64, 64),
                        pygame.Rect(block.x, block.y - 64, 64, 64),
                    ]
                    for neighbor in neighbors:
                        if (
                            0 <= neighbor.x < self.width
                            and 0 <= neighbor.y < self.height
                            and neighbor not in queue
                            and neighbor not in cluster
                        ):
                            queue.append(neighbor)

            if cluster:  # Добавляем только непустые кластеры
                self.features.append(cluster)

    def get_color(self):
        """Возвращает темно-серый цвет для отображения гор."""
        return (105, 105, 105)  # Темно-серый цвет

    def break_block(self, world_x, world_y, gameplay):
        """Логика разрушения серых гор с выпадением предметов."""
        for cluster in self.features:
            for block in cluster:
                if block.collidepoint(world_x, world_y):
                    cluster.remove(block)
                    # Создаем выпадающий предмет в центре разрушенного блока
                    dropped_item = DroppedItem(block.x + 32, block.y + 32, "gray_mountain_block")
                    if gameplay and hasattr(gameplay, 'dropped_items'):
                        gameplay.dropped_items.append(dropped_item)
                        print("Серая гора разрушена! Выпал серый блок!")
                    return True
        print("Блок не найден.")
        return False


    def draw(self, screen, camera_x, camera_y, flashlight, dark_biome):
        """Отрисовка серых гор на экране."""
        for cluster in self.features:
            for block in cluster:
                screen_x = block.x - camera_x
                screen_y = block.y - camera_y

                # Если в темном биоме, проверяем радиус фонаря
                if dark_biome.is_hero_in_biome(flashlight.hero):
                    if flashlight.is_on and flashlight.is_within_light(block):
                        screen.blit(self.texture, (screen_x, screen_y))
                else:
                    screen.blit(self.texture, (screen_x, screen_y))

class PurpleMountains:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.features = []  # Инициализируем список для хранения кластеров гор
        self.texture = pygame.image.load("gfx/purple_mountain.png")

    def generate_features(self, num_clusters, dark_biome):
        """Генерация фиолетовых гор, избегая пересечения с темным биомом."""
        for _ in range(num_clusters):
            cluster = []
            start_x = random.randint(0, self.width - 64)
            start_y = random.randint(0, self.height - 64)

            # Создаем начальный блок горы
            queue = [pygame.Rect(start_x, start_y, 64, 64)]
            while queue and len(cluster) < random.randint(10, 30):  # Размер кластера
                block = queue.pop(0)

                # Проверяем пересечение с темным биомом
                if not dark_biome.is_rect_in_biome(block):
                    cluster.append(block)

                    # Добавляем соседние блоки
                    neighbors = [
                        pygame.Rect(block.x + 64, block.y, 64, 64),
                        pygame.Rect(block.x - 64, block.y, 64, 64),
                        pygame.Rect(block.x, block.y + 64, 64, 64),
                        pygame.Rect(block.x, block.y - 64, 64, 64),
                    ]
                    for neighbor in neighbors:
                        if (
                            0 <= neighbor.x < self.width
                            and 0 <= neighbor.y < self.height
                            and neighbor not in queue
                            and neighbor not in cluster
                        ):
                            queue.append(neighbor)

            if cluster:  # Добавляем только непустые кластеры
                self.features.append(cluster)

    def get_color(self):
        """Возвращает темно-фиолетовый цвет для отображения гор."""
        return (75, 0, 130)  # Темно-фиолетовый цвет

    def break_block(self, world_x, world_y, gameplay):
        for cluster in self.features:
            for block in cluster:
                if block.collidepoint(world_x, world_y):
                    cluster.remove(block)
                    dropped_item = DroppedItem(block.x + 32, block.y + 32, "purple_mountain_block")
                    print(f"Создан DroppedItem: {dropped_item.item_type} на координатах ({dropped_item.x}, {dropped_item.y})")
                    if gameplay and hasattr(gameplay, 'dropped_items'):
                        gameplay.dropped_items.append(dropped_item)
                        print("Фиолетовый блок добавлен в dropped_items")
                    else:
                        print("Ошибка: gameplay или dropped_items отсутствует!")
                    return True
        print("Блок не найден.")
        return False



    def draw(self, screen, camera_x, camera_y, flashlight, dark_biome):
        """Отрисовка фиолетовых гор на экране."""
        for cluster in self.features:
            for block in cluster:
                screen_x = block.x - camera_x
                screen_y = block.y - camera_y

                # Если в темном биоме, проверяем радиус фонаря
                if dark_biome.is_hero_in_biome(flashlight.hero):
                    if flashlight.is_on and flashlight.is_within_light(block):
                        screen.blit(self.texture, (screen_x, screen_y))
                else:
                    screen.blit(self.texture, (screen_x, screen_y))