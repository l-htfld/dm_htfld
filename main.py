import pygame, sys
from pygame.locals import *
import random
from entities import Hero, EnemyMelee, EnemyArcher, Cursor, Inventory, CraftingTable, Animal, SpawnManager, AnimalSpawnManager, FinalBoss, Bullet
from graphics import Landscape, DarkBiome, Flashlight, DarkGrayMountains, PurpleMountains
from menu import StartMenu
import math

damage_timer = pygame.time.get_ticks()

class Gameplay:
    def __init__(self, map_width, map_height):
        self.FPS = 24
        self.FramePerSec = pygame.time.Clock()

        # Настройки экрана
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.map_width = map_width  # Ширина карты
        self.map_height = map_height  # Высота карты
        self.displaysurf = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # Цвета
        self.WHITE = (255, 255, 255)
        self.YELLOW = (255, 255, 0)
        self.GREEN = (0, 128, 0)
        self.RED = (128, 0, 0)
        self.ORANGE = (255, 128, 0)
        self.BLACK = (0, 0, 0)
        self.L_GREEN = (0, 255, 0)
        self.L_BLUE = (0, 0, 255)
        self.CYAN = (0, 255, 255)
        self.SHADOW = (64, 64, 64)

        #звуки
        self.scroll_sound = pygame.mixer.Sound("sound/menusnd01.wav")
        self.select_sound = pygame.mixer.Sound("sound/menusnd02.wav")
        self.die_sound = pygame.mixer.Sound("sound/boom-shipdie.wav")
        self.shoot_sound = pygame.mixer.Sound("sound/spathi-bullet.wav")
        self.impact_sound = pygame.mixer.Sound("sound/boom-tiny.wav")
        self.player_die_sound = pygame.mixer.Sound("sound/druuge-furnace.wav")
        self.footsteps_sound = pygame.mixer.Sound("sound/minecraft-footsteps.mp3")

        # Расчёт тайлов
        self.tilesX = int(self.SCREEN_WIDTH / 16)
        self.tilesY = int(self.SCREEN_HEIGHT / 16)
        self.brick = pygame.image.load("gfx/brick.png").convert()

        # Позиция камеры
        self.camera_x = 0
        self.camera_y = 0

        # Темный биом
        self.dark_biome = DarkBiome(7000, 7000, map_width, map_height)

        # Фонарь
        self.flashlight = Flashlight(hero)
        
        self.cursor = Cursor()
        
        # Список выпавших предметов
        self.dropped_items = []

        # Список врагов
        self.enemies = []
        
        # Список животных
        self.animals = []
        
        # Cgbcjr gekm
        self.bullets = []
        
        # Для хранения блоков, которые нужно разрушить
        self.blocks_to_break = []
        
        self.inventory = Inventory(x=50, y=650, cell_size=50, capacity=9)
        self.hero_has_pistol = 1    
        
        self.boss_spawned = False
        self.final_boss = None    

    # Рисуем инвентарь
    def draw_inventory(self):
        self.inventory.render(self.displaysurf)

    def quitGame(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and event.mod & pygame.KMOD_CTRL:
                    pygame.quit()
                    sys.exit()
                    
    
    def spawn_enemy(self, enemy_type, landscape):
        while True:
            # Случайные координаты на карте
            x = random.randint(0, self.map_width)
            y = random.randint(0, self.map_height)

            # Проверка на пересечение с горными массивами
            if not any(
                pygame.Rect(x, y, 32, 32).colliderect(segment)
                for cluster in landscape.mountains for segment in cluster
            ):
                # Проверяем, чтобы враг не спавнился в зоне видимости камеры
                if not (self.camera_x <= x <= self.camera_x + self.SCREEN_WIDTH and
                        self.camera_y <= y <= self.camera_y + self.SCREEN_HEIGHT):
                    if enemy_type == "archer":
                        self.enemies.append(EnemyArcher(hp=100, power=20, x=x, y=y, speed=4, protect=5, fov_radius=200, active=1))
                    elif enemy_type == "melee":
                        self.enemies.append(EnemyMelee(hp=100, power=20, x=x, y=y, speed=4, protect=5, fov_radius=200, active=1))
                    break
                
    def spawn_animal(self, num_animals, hero):
        """Создает заданное количество животных."""
        for _ in range(num_animals):
            x = random.randint(0, self.map_width)
            y = random.randint(0, self.map_height)
            speed = random.uniform(2, 4)  # Скорость животного
            animal = Animal(hp=25, power=0, x=x, y=y, speed=speed)  # Животное с HP 25 и без атаки
            self.animals.append(animal)
            print(f"Создано животное на ({x}, {y}).")
            
    def spawn_final_boss(self, hero):
        if not self.boss_spawned:
            x, y = hero.x + 500, hero.y + 500  # Рядом с героем
            self.final_boss = FinalBoss(hp=300, power=9, x=x, y=y, speed=2)
            self.boss_spawned = True
            print("Финальный босс появился!")

    def handleHeroCollisionForEnemies(self, enemies, hero):
        """Обрабатывает столкновение врагов с героем."""
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32) # Создаем прямоугольник героя для проверки столкновений
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 32, 32) # Создаем прямоугольник врага для проверки столкновений
            if hero_rect.colliderect(enemy_rect):
                if enemy_rect.right > hero_rect.left and enemy_rect.left < hero_rect.right: # Если правый край врага пересекает левый край героя (и наоборот)
                    if enemy_rect.bottom > hero_rect.top: # Если низ врага пересекает верх героя, враг перемещается выше героя
                        enemy.y = hero_rect.top - enemy_rect.height
                    elif enemy_rect.top < hero_rect.bottom: # Если верх врага пересекает низ героя, враг перемещается ниже героя
                        enemy.y = hero_rect.bottom
                elif enemy_rect.bottom > hero_rect.top and enemy_rect.top < hero_rect.bottom: # Если верх и низ врага пересекаются с верхом и низом героя
                    if enemy_rect.right > hero_rect.left:
                        enemy.x = hero_rect.left - enemy_rect.width
                    elif enemy_rect.left < hero_rect.right:
                        enemy.x = hero_rect.right
                        
    def handle_attack(self, hero):
        """Обрабатывает атаку героя по врагам."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = mouse_x + self.camera_x
        world_y = mouse_y + self.camera_y

        for enemy in self.enemies:
            if enemy.is_alive:
                # Проверяем расстояние до врага
                distance = math.hypot(enemy.x - hero.x, enemy.y - hero.y)
                if distance <= 50:  # Ближний бой, враг в радиусе 50 пикселей
                    # Проверяем, попадает ли клик в хитбокс врага
                    if pygame.Rect(enemy.x - 16, enemy.y - 16, 32, 32).collidepoint(world_x, world_y):
                        print("Удар по врагу!")
                        enemy.take_damage()
                        enemy.knockback(hero)
                        if not enemy.is_alive:
                            print("Враг уничтожен!")
                            self.enemies.remove(enemy)
                        return
        print("Нет врага для атаки!")
                    
    def moveCharacter(self, hero, *landscapes):
        keys = pygame.key.get_pressed()
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32)
        hero_is_moving = False  # Флаг движения героя

        all_segments = []
        for landscape in landscapes:
            if hasattr(landscape, 'mountains'):
                for cluster in landscape.mountains:
                    all_segments.extend(cluster)
            elif hasattr(landscape, 'features'):
                for feature in landscape.features:
                    all_segments.extend(feature)

        enemy_rects = [pygame.Rect(enemy.x, enemy.y, 32, 32) for enemy in self.enemies]
        obstacles = all_segments + enemy_rects 

        def move_enemy(enemy, dx, dy):
            enemy_rect = pygame.Rect(enemy.x, enemy.y, 32, 32)
            new_enemy_rect = enemy_rect.move(dx, dy)
            if not any(new_enemy_rect.colliderect(obstacle) for obstacle in all_segments) and not new_enemy_rect.colliderect(hero_rect):
                enemy.x += dx
                enemy.y += dy
                return True
            return False

        # Движения героя
        if keys[pygame.K_w]:
            new_rect = hero_rect.move(0, -hero.speed) # Создаем новый прямоугольник, который показывает предполагаемую новую позицию героя
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)] # Проверяем, есть ли препятствия, с которыми столкнется герой при движении вверх
            if not collision_segments:
                hero.y -= hero.speed # Если препятствий нет, герой может двигаться вверх
                hero_is_moving = True  # Герой двигается
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.top - s.bottom))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment) # Если ближайшее препятствие — враг, пытаемся переместить врага
                    if move_enemy(self.enemies[enemy_index], 0, -hero.speed): # Если враг смог сдвинуться, герой тоже сдвигается
                        hero.y -= hero.speed
                else:
                    hero.y = nearest_segment.bottom # Если ближайшее препятствие не враг, корректируем позицию героя по нижнему краю препятствия

        # С остальными также

        if keys[pygame.K_s]:
            new_rect = hero_rect.move(0, hero.speed)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.y += hero.speed
                hero_is_moving = True  # Герой двигается
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.bottom - s.top))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], 0, hero.speed):
                        hero.y += hero.speed
                else:
                    hero.y = nearest_segment.top - hero_rect.height

        if keys[pygame.K_a]:
            new_rect = hero_rect.move(-hero.speed, 0)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.x -= hero.speed
                hero_is_moving = True  # Герой двигается
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.left - s.right))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], -hero.speed, 0):
                        hero.x -= hero.speed
                else:
                    hero.x = nearest_segment.right

        if keys[pygame.K_d]:
            new_rect = hero_rect.move(hero.speed, 0)
            collision_segments = [obstacle for obstacle in obstacles if new_rect.colliderect(obstacle)]
            if not collision_segments:
                hero.x += hero.speed
                hero_is_moving = True  # Герой двигается
            else:
                nearest_segment = min(collision_segments, key=lambda s: abs(hero_rect.right - s.left))
                if nearest_segment in enemy_rects:
                    enemy_index = enemy_rects.index(nearest_segment)
                    if move_enemy(self.enemies[enemy_index], hero.speed, 0):
                        hero.x += hero.speed
                else:
                    hero.x = nearest_segment.left - hero_rect.width

        # Update camera position
        self.camera_x = max(0, hero.x - self.SCREEN_WIDTH // 2)
        self.camera_y = max(0, hero.y - self.SCREEN_HEIGHT // 2)

        if keys[pygame.K_i]:
            print (dungeon.inventory.items)
        
        return hero_is_moving  # Возвращаем флаг движения

        
    def renderCursor(self):
        self.cursor.draw(self.displaysurf, self.camera_x, self.camera_y)

    def tileBackground(self, texture):
        for x in range(self.tilesX):
            for y in range(self.tilesY):
                self.displaysurf.blit(texture, (x * 32, y * 32))
                
    def renderBullet(self, color, bullet):
        """Отрисовка пули на экране."""
        pygame.draw.rect(
            self.displaysurf,
            color,
            pygame.Rect(
                bullet.x - self.camera_x,
                bullet.y - self.camera_y,
                8,  # Ширина пули
                8,  # Высота пули
            ),
        )

    def playerShoot (self, hero):

        if self.hero_has_pistol == 1:

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.shoot_sound.play ()
                    hero.shoot (1)
                if event.key == pygame.K_UP:
                    self.shoot_sound.play ()
                    hero.shoot (4)
                if event.key == pygame.K_RIGHT:
                    self.shoot_sound.play ()
                    hero.shoot (3)
                if event.key == pygame.K_DOWN:
                    self.shoot_sound.play ()
                    hero.shoot (2)

    def renderHero(self, color, hero):
        pygame.draw.rect(self.displaysurf, color, pygame.Rect(hero.x - self.camera_x, hero.y - self.camera_y, 32, 32))

    def renderEnemy(self, color, enemy):
        if enemy.active:
            pygame.draw.rect(self.displaysurf, color, pygame.Rect(enemy.x - self.camera_x, enemy.y - self.camera_y, 32, 32))
        if enemy.hp < 100:
            pygame.draw.rect(self.displaysurf, self.L_GREEN, pygame.Rect(enemy.x - self.camera_x, enemy.y - self.camera_y - 8, int(0.32 * enemy.hp), 5))

    def renderDarkBiome(self):
        self.dark_biome.draw(self.displaysurf, self.camera_x, self.camera_y, self.flashlight)

    def renderFlashlight(self):
        self.flashlight.draw(self.displaysurf, self.camera_x, self.camera_y)
        
    
    def handle_mouse_click(self, cursor, landscape, inventory):
        """Обработка клика мыши для разрушения гор."""
        world_x = cursor.world_x
        world_y = cursor.world_y

        # Получаем выбранный предмет
        selected_item = inventory.get_selected_item()
        print(f"Выбранный предмет: {selected_item}")  # Отладка: проверяем текущий выбранный предмет

        # Устанавливаем, можно ли ломать серые горы
        can_break_gray_mountain = selected_item == "pickaxe"

        # Перебираем все кластеры в ландшафте
        for cluster in landscape.mountains:
            for block in cluster:
                if block.collidepoint(world_x, world_y):  # Проверяем, попадает ли клик в блок
                    if hasattr(block, "type") and block.type == "gray_mountain":
                        if not can_break_gray_mountain:
                            print("Нужна кирка для разрушения серой горы!")
                            return  # Нельзя ломать серую гору без кирки
                        else:
                            print("Серая гора разрушена киркой!")

                    # Если это не серая гора, разрушаем блок
                    else:
                        print("Блок разрушен.")

                    # Удаляем блок из кластера
                    cluster.remove(block)
                    return

        # Если курсор не попал в блок
        print("Блок не найден под курсором.")
        
        
if __name__ == '__main__':
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("Dungeon Sandbox")
    font = pygame.font.SysFont("Pixel Font", 24)
    
    # Инициализация звука геймплея
    pygame.mixer.init()
    pygame.mixer.music.load(r"sound\sondtrack_game.mp3")  # Загружаем фоновую музыку
    pygame.mixer.music.set_volume(0.5)  # Устанавливаем громкость
    pygame.mixer.music.play(-1)  # Запускаем музыку зацикленно
    
    # Загрузка звука шагов
    hero_steps_sound = pygame.mixer.Sound(r"sound\heroes_steps.mp3")
    hero_steps_sound.set_volume(0.7)  # Настраиваем громкость
    
    # Инициализация звука меню
    menu_soundtrack = pygame.mixer.Sound(r"sound\menu_soundtrack.mp3")
    menu_soundtrack_channel = pygame.mixer.Channel(2)  # Используем отдельный канал для меню
    
    def draw_text(surface, text, font, color, position):
        """Рисует текст на экране."""
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, position)

    # Создание главного героя
    hero = Hero(hp=100, power=20, x=640, y=360, speed=21, protect=5, active=1)  # Начальная позиция героя в центре

    # Задаем размеры карты
    map_width = 10000  # Ширина карты
    map_height = 10000  # Высота карты

    # Создание темного биома
    dark_biome = DarkBiome(7000, 7000, map_width, map_height)  # Указываем координаты и размер темного биома

    # Создание ландшафта
    landscape = Landscape(map_width, map_height)  # Полный размер карты
    landscape.generate_mountains(random.randint(100, 170), dark_biome)  # Генерация от 100 до 170 гор
    
    dark_gray_mountains = DarkGrayMountains(width=10000, height=10000)
    dark_gray_mountains.generate_features(num_clusters=50, dark_biome=dark_biome)
    
    dark_purple_mountains = PurpleMountains(width=10000, height=10000)
    dark_purple_mountains.generate_features(num_clusters=50, dark_biome=dark_biome)
    
    inventory = Inventory(x=50, y=650, cell_size=50, capacity=9)

    # Создание фонарика
    flashlight = Flashlight(hero)

    # Создание игрового процесса
    dungeon = Gameplay(map_width, map_height)
    
    # Спавним 100 животных
    dungeon.spawn_animal(100, hero)
    
    animal_spawn_manager = AnimalSpawnManager(map_width, map_height, dark_biome)
    print(f"Список животных перед инициализацией: {len(dungeon.animals)}")
    animal_spawn_manager.initialize_counts(dungeon.animals)
    
    # Добавляем верстак
    crafting_table = CraftingTable(x=400, y=200, cell_size=50)
    crafting_open = False

    # Спавним случайное количество врагов
    for _ in range(random.randint(100, 105)):  # Генерация от 5 до 25 врагов
        enemy_type = random.choice(["melee", "archer"])
        dungeon.spawn_enemy(enemy_type, landscape)
        
    spawn_manager = SpawnManager(map_width, map_height, dark_biome)
    spawn_manager.initialize_counts(dungeon.enemies)  # Передаем список врагов
        
    # Устанавливаем иконку игры
    pygame.display.set_icon(pygame.transform.scale(pygame.image.load('gfx/brick.png'), (32, 32)))

    clock = pygame.time.Clock()

    running = True
    is_hero_attacking = False
    crafting_open = False  # Флаг для отображения верстака
    dragging_item = None  # Перетаскиваемый предмет
    paused = False  # Переменная для отслеживания состояния паузы
    
    def draw_pause_menu(screen, font_path, background_path, screen_width, screen_height):
        """Отрисовка меню паузы с изменением стиля текста и использованием изображения фона."""
        font_size = 36  # Размер шрифта
        font = pygame.font.Font(font_path, font_size)

        # Загружаем изображение фона
        pause_background = pygame.image.load(background_path).convert()
        pause_background = pygame.transform.scale(pause_background, (screen_width, screen_height))
        screen.blit(pause_background, (0, 0))

        # Настройки текста
        options = ["1. Продолжить", "2. Выход"]
        colors = {"text": (255, 255, 255), "outline": (0, 0, 0)}  # Белый текст с черной обводкой
        y_offset = screen_height // 3  # Расстояние от верха экрана

        for i, option in enumerate(options):
            text_surface = font.render(option, True, colors["text"])
            outline_surface = font.render(option, True, colors["outline"])

            # Координаты для центрирования текста
            text_x = (screen_width - text_surface.get_width()) // 2
            text_y = y_offset + i * 60  # Расстояние между строками

            # Рисуем обводку (черный контур)
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:  # Смещение для контура
                screen.blit(outline_surface, (text_x + dx, text_y + dy))

            # Рисуем основной текст
            screen.blit(text_surface, (text_x, text_y))



    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused  # Переключаем состояние паузы

                # Логика управления меню паузы
                if paused:
                    if event.key == pygame.K_1:  # Продолжить
                        paused = False
                    elif event.key == pygame.K_2:  # Выход
                        running = False

                if not paused:
                    # Обработка выбора ячейки
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        inventory.handle_key_press(event.key)  # Выбор ячейки

                    # Открытие/закрытие верстака
                    elif event.key == pygame.K_i:
                        crafting_open = not crafting_open  # Переключаем состояние верстака
                        print(f"Верстак открыт: {crafting_open}")

                    # Крафт, если верстак открыт
                    elif crafting_open and event.key == pygame.K_c:
                        crafted_item = crafting_table.craft()
                        if crafted_item:
                            inventory.add_item(crafted_item)  # Добавляем созданный предмет в инвентарь
                            print(f"Создан предмет: {crafted_item}, текущее состояние инвентаря: {inventory.items}")

            # Перетаскивание предметов или атака
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Левая кнопка
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if crafting_open:
                    if not dragging_item:
                        # Проверяем инвентарь
                        success, dragging_item = dungeon.inventory.handle_click(mouse_x, mouse_y)
                        # Если не из инвентаря, проверяем верстак
                        if not success:
                            _, dragging_item = crafting_table.handle_click(mouse_x, mouse_y)
                else:
                    # Выполняем действия в игровом мире
                    world_x = dungeon.cursor.world_x
                    world_y = dungeon.cursor.world_y

                    # Проверяем выбранный предмет
                    selected_item = inventory.get_selected_item()
                    print(f"Выбранный предмет: {selected_item}")  # Отладка

                    # Сначала проверяем взаимодействие с врагами и боссом
                    enemy_attacked = False
                    boss_attacked = False

                    if hero.perform_melee_attack(dungeon.enemies, landscape, selected_item, boss=dungeon.final_boss):
                        print("Цель атакована!")
                        enemy_attacked = True

                    # Проверяем атаку босса отдельно
                    if not enemy_attacked and selected_item in ("sword", 'gray_sword', "pickaxe", None):
                        if dungeon.final_boss and dungeon.final_boss.is_alive:
                            distance_to_boss = math.hypot(dungeon.final_boss.x - hero.x, dungeon.final_boss.y - hero.y)
                            if distance_to_boss <= 32:  # Радиус ближнего боя
                                damage = {"sword": 7, "gray_sword": 9, "pickaxe": 5, None: 3}.get(selected_item, 3)
                                dungeon.final_boss.take_damage(damage)
                                print(f"Босс атакован! Осталось HP: {dungeon.final_boss.hp}")
                                boss_attacked = True
                        
        
                    # Затем проверяем взаимодействие с животными
                    animal_attacked = False
                    if not enemy_attacked and selected_item in ("sword", 'gray_sword', "pickaxe", None):  # Урон животным любым предметом или рукой
                        for animal in dungeon.animals:
                            distance = math.hypot(animal.x - hero.x, animal.y - hero.y)
                            if distance <= 50:  # Радиус ближнего боя
                                damage = {"sword": 3,  "gray_sword": 5, "pickaxe": 2, None: 1}[selected_item]
                                animal.take_damage(damage, hero)
                                print(f"Животное ранено! Осталось HP: {animal.hp}")
                                animal_attacked = True
                                break  # Прерываем, чтобы обработать только одно животное

                    # Если не было взаимодействия с врагами, животными или боссом, проверяем объекты
                    if not enemy_attacked and not animal_attacked:
                        if selected_item == "gray_pickaxe":
                            # Ломание темно-фиолетовых, серых или коричневых гор серой киркой
                            if dark_purple_mountains.break_block(world_x, world_y, dungeon):
                                print("Темно-фиолетовый блок разрушен серой киркой!")
                            elif dark_gray_mountains.break_block(world_x, world_y, dungeon):
                                print("Серая гора разрушена серой киркой!")
                            elif landscape.break_block(world_x, world_y, dungeon):
                                print("Коричневый блок разрушен серой киркой.")
                            else:
                                print("Блок не найден под курсором.")
                        elif selected_item == "pickaxe":
                            # Ломание серых или коричневых гор обычной киркой
                            if dark_gray_mountains.break_block(world_x, world_y, dungeon):
                                print("Серая гора разрушена киркой!")
                            elif landscape.break_block(world_x, world_y, dungeon):
                                print("Коричневый блок разрушен киркой.")
                            else:
                                print("Блок не найден под курсором.")
                        else:
                            # Ломание только коричневых гор
                            if landscape.break_block(world_x, world_y, dungeon):
                                print("Блок разрушен!")
                            else:
                                print("Блок не найден под курсором.")

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Правая кнопка
                # Вызов финального босса с использованием final_stick
                selected_item = inventory.get_selected_item()
                if selected_item == "final_stick" and not dungeon.boss_spawned:
                    inventory.remove_selected_item()  # Удаляем палку из инвентаря
                    dungeon.spawn_final_boss(hero)  # Вызываем босса
                    print("Финальный босс призван!")

                                


            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Отпускание
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if crafting_open and dragging_item:
                    # Сначала пытаемся положить на верстак
                    success, dragging_item = crafting_table.handle_click(mouse_x, mouse_y, dragging_item)
                    if not success:
                        # Если не удалось, пробуем вернуть в инвентарь
                        _, dragging_item = dungeon.inventory.handle_click(mouse_x, mouse_y, dragging_item)
                        
                        
        pause_background = pygame.image.load("gfx/pause_background.jpg").convert()
        pause_background = pygame.transform.scale(pause_background, (dungeon.SCREEN_WIDTH, dungeon.SCREEN_HEIGHT))

        pixel_font_path = r"font\minecraft.ttf"
        pause_background_path = r"gfx\pause_background.jpg"

        if paused:
            draw_pause_menu(
                screen=dungeon.displaysurf,
                font_path=pixel_font_path,
                background_path=pause_background_path,
                screen_width=dungeon.SCREEN_WIDTH,
                screen_height=dungeon.SCREEN_HEIGHT,
            )  # Передаем дисплей и глобальный шрифт
            pygame.display.flip()
            clock.tick(dungeon.FPS)
            # Проигрывание трека меню
            if not menu_soundtrack_channel.get_busy():
                menu_soundtrack_channel.play(menu_soundtrack, loops=-1)
                pygame.mixer.music.stop()
            
            continue
        
        else:
            # Останавливаем трек меню, если паузы нет
            if menu_soundtrack_channel.get_busy():
                menu_soundtrack_channel.stop()
                pygame.mixer.music.play(-1)
        
        # Проверка респавна врагов
        spawn_manager.update(dungeon.enemies)
        animal_spawn_manager.update(dungeon.animals)

        # Обновление позиции героя
        dungeon.moveCharacter(hero, landscape, dark_gray_mountains, dark_purple_mountains)
        
        dungeon.hero_is_moving = dungeon.moveCharacter(hero, landscape, dark_gray_mountains, dark_purple_mountains)
        
        hero_steps_channel = pygame.mixer.Channel(1)
        
        # Проверка, двигается ли герой
        if dungeon.hero_is_moving:
            if not hero_steps_channel.get_busy():  # Если звук не играет, запускаем
                hero_steps_channel.play(hero_steps_sound, loops=-1)  # Запускаем звук шагов в цикле
        else:
            hero_steps_channel.stop()  # Останавливаем звук, если герой не двигается
        hero.update_rect()

        # Проверка, находится ли герой в темном биоме
        if dark_biome.is_hero_in_biome(hero):
            flashlight.is_on = True  # Включаем фонарик, если герой в темном биоме
        else:
            flashlight.is_on = False  # Иначе выключаем фонарик

        # Отрисовка интерфейса
        dungeon.tileBackground(dungeon.brick)

        # Отрисовка ландшафта с учетом камеры
        landscape.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight, dark_biome)
        dark_gray_mountains.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight, dark_biome)
        dark_purple_mountains.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight, dark_biome)

        # Отрисовка темного биома с учетом смещения камеры
        dark_biome.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y, flashlight)

        # Обновление и отрисовка курсора
        dungeon.cursor.update(dungeon.camera_x, dungeon.camera_y)  # Обновляем мировые координаты курсора
        dungeon.cursor.draw(dungeon.displaysurf)  # Отрисовываем курсор

        # Обновление врагов
        for enemy in dungeon.enemies:
            enemy.update(hero, [landscape, dark_gray_mountains, dark_purple_mountains], hero_attacking=is_hero_attacking)  # Передаем героя врагу

            # Проверка столкновений врагов с героем
            dungeon.handleHeroCollisionForEnemies(dungeon.enemies, hero)
            
            current_time = pygame.time.get_ticks()
            if current_time - damage_timer >= 1000:  # Каждую секунду
                for enemy in dungeon.enemies:
                    distance_to_hero = math.hypot(enemy.x - hero.x, enemy.y - hero.y)
                    if distance_to_hero <= 32:  # Если враг вплотную к герою
                        hero.take_damage(2)  # Урон от врага
                        print(f"Герой получил урон от врага! Текущее HP: {hero.hp}")
                        damage_timer = current_time  # Сбрасываем таймер

            # Обновление и отрисовка пуль, с проверкой таймера на уничтожение
            if isinstance(enemy, EnemyArcher) and enemy.bullets and enemy.bullet.update(dungeon, hero):
                dungeon.renderBullet(dungeon.WHITE, enemy.bullet)
            else:
                enemy.bullet = None  # Удаляем пулю, если она "умерла"
                
        if dungeon.final_boss:
            if dungeon.final_boss.is_alive:
                dungeon.final_boss.update(hero, obstacles, dungeon)  # Обновляем поведение босса
                dungeon.final_boss.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)  # Отрисовываем босса
            else:
                print("Босс мертв, удаляем его из игры.")
                dungeon.final_boss = None  # Удаляем босса

        # Отрисовка выпавших предметов
        for item in dungeon.dropped_items:
            item.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)
            

        # Проверяем сбор предметов
        for item in dungeon.dropped_items[:]:
            if hero.rect.colliderect(item.rect):
                print(f"Попытка собрать предмет: {item.item_type}")
                if item.item_type == "purple_mountain_block":
                    if dungeon.inventory.add_item(item.item_type):
                        print(f"Собран предмет: {item.item_type}")
                        dungeon.dropped_items.remove(item)  # Убираем предмет с карты
                    else:
                        print(f"Инвентарь полон! Предмет {item.item_type} остается на карте.")
                else:
                    if dungeon.inventory.add_item(item.item_type):
                        print(f"Собран предмет: {item.item_type}")
                        dungeon.dropped_items.remove(item)  # Убираем предмет с карты
                    else:
                        print(f"Инвентарь полон! Предмет {item.item_type} остается на карте.")

            
            
        # Отрисовка интерфейса
        if crafting_open:
            # Отрисовка верстака
            crafting_table.render(dungeon.displaysurf, dungeon.inventory.get_item_icon)
            # Отрисовка инвентаря (чтобы был виден весь интерфейс)
            dungeon.inventory.render(dungeon.displaysurf)
        else:
            # Отрисовка только инвентаря, если верстак закрыт
            dungeon.inventory.render(dungeon.displaysurf)
            
        # Отрисовка полоски здоровья героя
        hero.draw_health_bar(
            screen=dungeon.displaysurf,
            max_width=200,  # Максимальная ширина полоски
            height=20,      # Высота полоски
            screen_width=dungeon.SCREEN_WIDTH,
            screen_height=dungeon.SCREEN_HEIGHT,
        )

        # Отрисовка всех объектов на экране
        dungeon.renderHero(dungeon.GREEN, hero)
        if hero.bullet and hero.bullet.update():
            dungeon.renderBullet(dungeon.WHITE, hero.bullet)
            
            
        for enemy in dungeon.enemies:
            if isinstance(enemy, EnemyMelee):
                dungeon.renderEnemy(dungeon.RED, enemy)
            elif isinstance(enemy, EnemyArcher):
                dungeon.renderEnemy(dungeon.ORANGE, enemy)
                
            
        obstacles = []
        for cluster in landscape.mountains + dark_gray_mountains.features + dark_purple_mountains.features:
            obstacles.extend([segment for segment in cluster if isinstance(segment, pygame.Rect)])
        obstacles.append(pygame.Rect(hero.x, hero.y, 32, 32))  # Герой как препятствие


        # Удаляем животных с HP <= 0
        dungeon.animals = [animal for animal in dungeon.animals if animal.hp > 0]
        
        # Обновление животных
        for animal in dungeon.animals:
            animal.update(hero, obstacles)  # Обновляем поведение животного

        # Отрисовка животных
        for animal in dungeon.animals:
            pygame.draw.rect(dungeon.displaysurf, (255, 255, 255), (animal.x - dungeon.camera_x, animal.y - dungeon.camera_y, 32, 32))

            
        # Обновление и отрисовка пуль босса
        if dungeon.final_boss:  # Если босс существует
            for bullet in dungeon.final_boss.bullets[:]:  # Перебираем пули босса
                if not bullet.update(hero):  # Проверяем обновление (например, столкновение с героем)
                    dungeon.final_boss.bullets.remove(bullet)  # Удаляем пулю
                else:
                    bullet.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)  # Отрисовываем пулю
                    
        
        
        # Отрисовка фонарика
        flashlight.draw(dungeon.displaysurf, dungeon.camera_x, dungeon.camera_y)

        # Отрисовка
        inventory.render(dungeon.displaysurf)
        #inventory.items[0] = "pickaxe"
        
        # Отображение HP героя
        hp_text = f"HP: {hero.hp}"
        text_position = (dungeon.SCREEN_WIDTH - 80, dungeon.SCREEN_HEIGHT - 60)  # Позиция в правом нижнем углу
        draw_text(dungeon.displaysurf, hp_text, font, (255, 255, 255), text_position)
        
        # Обновление экрана
        pygame.display.flip()

        # Ограничение FPS
        clock.tick(dungeon.FPS)

    pygame.quit()

