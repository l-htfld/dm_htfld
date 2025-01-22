import math
import pygame, sys
from pygame.locals import *
import numpy as np
import random

TIME_INTERVAL = 2000  # 2 секунды для отслеживания времени столкновения
last_hit_time = 0  # Время последнего столкновения с врагом

class Entity: # Родительский класс
    def __init__(self, hp, power, x, y, speed, active) -> None:
        self.hp = hp
        self.power = power
        self.speed = speed
        self.x = x
        self.y = y
        self.active = active

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        print(f"{self.__class__.__name__} погиб")


class Hero(Entity):
    def __init__(self, hp, power, x, y, speed, protect, active) -> None:
        super().__init__(hp, power, x, y, speed, active)
        self.protect = protect
        self.bullet = None
        self.speed = speed
        self.rect = pygame.Rect(self.x, self.y, 32, 32)
        self.max_hp = hp
        
    def update(self):
        """Обновление состояния героя."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time > TIME_INTERVAL:
            self.last_hit_time = current_time
            
    def take_damage_from_enemy(self, amount):
        """Отнимает HP при столкновении с врагом, если прошло 2 секунды."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time > TIME_INTERVAL:
            self.hp -= amount
            self.last_hit_time = current_time  # Обновляем время последнего столкновения
            print(f"Герой получил урон! Осталось HP: {self.hp}")
            
    def restore_hp(self, amount):
        """Восстановление HP герою при убийстве животного."""
        self.hp += amount
        if self.hp > 20:  # Максимум 20 HP
            self.hp = 20
        print(f"Герой восстановил {amount} HP! Текущее HP: {self.hp}")

    def shoot(self, direction):
        if self.power >= 5:
            self.bullet = PlayerBullet(self.x, self.y, direction)
            self.power -= 1

    def updatePower (self):
        if self.power < 15:
            self.power += 5
        else: 
            self.power = 20
                
    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y
        
    def perform_melee_attack(self, enemies, landscape, selected_item=None, boss=None):
        """Атака врагов, босса или разрушение объектов в зависимости от выбранного предмета."""
        # Определяем урон в зависимости от предмета
        if selected_item == "sword":
            damage = 7
            item_name = "мечом"
        elif selected_item == "pickaxe":
            damage = 5
            item_name = "киркой"
        elif selected_item == "gray_sword":
            damage = 9
            item_name = "серым мечом"    
        else:
            damage = 3
            item_name = "рукой"

        # Атака врагов
        for enemy in enemies:
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            print(f"Проверяем врага: {enemy.__class__.__name__}, расстояние: {distance}")  # Отладка
            if distance <= 50:  # Радиус ближнего боя
                print(f"Удар по врагу {enemy.__class__.__name__} {item_name}!")
                enemy.take_damage(damage)  # Наносим урон врагу
                enemy.knockback(self)  # Отталкиваем врага
                if enemy.hp <= 0:
                    print(f"{enemy.__class__.__name__} уничтожен!")
                    enemies.remove(enemy)  # Убираем врага из списка
                return True  # Успешный удар

        # Атака босса
        if boss and boss.is_alive:
            distance_to_boss = math.hypot(boss.x - self.x, boss.y - self.y)
            print(f"Проверяем босса: расстояние {distance_to_boss}")  # Отладка
            if distance_to_boss <= 100:  # Радиус ближнего боя
                print(f"Удар по боссу {item_name}!")
                boss.take_damage(damage)
                if not boss.is_alive:
                    print("Финальный босс повержен!")
                return True

        print("Нет врагов или босса в радиусе атаки.")
        return False
    
    def heal(self, amount):
        """Восстанавливает HP героя."""
        self.hp = min(self.hp + amount, 100)  # Максимум здоровья ограничен 100
        print(f"Герой восстановил {amount} HP. Текущее здоровье: {self.hp}")
        
    def draw_health_bar(self, screen, max_width, height, screen_width, screen_height):
        """Отрисовывает полоску здоровья героя."""
        # Параметры полоски
        x = screen_width - max_width - 20  # Смещение от правого края
        y = screen_height - height - 20  # Смещение от нижнего края
        health_ratio = self.hp / self.max_hp  # Доля оставшегося здоровья

        # Рамка полоски
        pygame.draw.rect(screen, (255, 255, 255), (x, y, max_width, height), 2)  # Белая рамка

        # Полоска здоровья
        current_width = int(max_width * health_ratio)
        pygame.draw.rect(screen, (0, 255, 0), (x, y, current_width, height))  # Зеленая заливка
    

class AnimalNeuralNet:
    def __init__(self, input_size=4, hidden_size=6, output_size=2):
        self.weights = {
            'w1': np.random.randn(input_size, hidden_size),
            'b1': np.random.randn(hidden_size),
            'w2': np.random.randn(hidden_size, output_size),
            'b2': np.random.randn(output_size)
        }

    def forward(self, inputs):
        # Прямое распространение
        z1 = np.dot(inputs, self.weights['w1']) + self.weights['b1']
        a1 = np.tanh(z1)
        z2 = np.dot(a1, self.weights['w2']) + self.weights['b2']
        return np.tanh(z2)  # Возвращаем предсказанные движения (dx, dy)

class Animal(Entity):
    def __init__(self, hp, power, x, y, speed):
        super().__init__(hp, power, x, y, speed, active=0)  # Животное по умолчанию не активно
        self.type = "animal"
        self.is_fleeing = False  # Убегает ли животное от героя
        self.rect = pygame.Rect(x, y, 32, 32)
        self.neural_net = AnimalNeuralNet()  # Создаем нейронную сеть
        self.vision_radius = 200  # Радиус зрения животного
        self.random_dx = 0  # Случайное движение по X
        self.random_dy = 0  # Случайное движение по Y
        self.move_timer = 0  # Таймер для движения
        self.stop_timer = random.randint(30, 120)  # Время остановки (в кадрах)

    def flee_from_hero(self, hero):
        """Логика убегания животного от героя."""
        dx = self.x - hero.x
        dy = self.y - hero.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance > 0:
            dx /= distance
            dy /= distance

        # Убегаем на основе скорости
        self.x += dx * self.speed
        self.y += dy * self.speed

        print(f"{self.__class__.__name__} убегает от героя! Новая позиция: ({self.x}, {self.y})")

    def update(self, hero, obstacles):
        """Обновление состояния животного, включая столкновения и случайные движения."""
        dx = hero.x - self.x
        dy = hero.y - self.y
        distance = math.hypot(dx, dy)

        if distance < 100:  # Если герой рядом, животное пытается убежать
            if distance != 0:
                dx /= distance
                dy /= distance

            # Попытка убежать в противоположном направлении
            new_x = self.x - dx * self.speed
            new_y = self.y - dy * self.speed
            self.move_timer = 0  # Сбрасываем таймер остановки, животное в панике
        else:
            # Если животное далеко от героя
            if self.move_timer > 0:  # Если таймер движения активен
                new_x = self.x + self.random_dx * self.speed
                new_y = self.y + self.random_dy * self.speed
                self.move_timer -= 1
            else:  # Животное стоит на месте
                self.stop_timer -= 1
                new_x, new_y = self.x, self.y
                if self.stop_timer <= 0:  # Таймер остановки закончился
                    self.stop_timer = random.randint(30, 120)  # Устанавливаем новый таймер
                    self.move_timer = random.randint(30, 90)  # Устанавливаем новый таймер движения
                    self.random_dx = random.uniform(-1, 1)
                    self.random_dy = random.uniform(-1, 1)

        # Проверяем столкновения с препятствиями
        if self.check_collision(new_x, self.y, obstacles):
            if not self.check_collision(self.x, self.y + self.speed, obstacles):
                new_y = self.y + self.speed
            elif not self.check_collision(self.x, self.y - self.speed, obstacles):
                new_y = self.y - self.speed
            else:
                new_x = self.x  # Остаемся на месте по X

        if self.check_collision(self.x, new_y, obstacles):
            if not self.check_collision(self.x + self.speed, self.y, obstacles):
                new_x = self.x + self.speed
            elif not self.check_collision(self.x - self.speed, self.y, obstacles):
                new_x = self.x - self.speed
            else:
                new_y = self.y  # Остаемся на месте по Y

        # Если позиции не изменились, сохраняем их без тряски
        if abs(new_x - self.x) > 0.1 or abs(new_y - self.y) > 0.1:
            self.x = new_x
            self.y = new_y

        # Обновляем хитбокс
        self.rect.topleft = (self.x, self.y)
        
    def check_collision(self, x, y, obstacles):
        """Проверяет столкновение с препятствиями и героем."""
        test_rect = pygame.Rect(x, y, 32, 32)
        for obstacle in obstacles:
            if test_rect.colliderect(obstacle):
                return True
        return False

    def take_damage(self, amount, hero):
        """Получение урона с отскоком."""
        self.hp -= amount
        print(f"Животное ранено! HP: {self.hp}")
        if self.hp <= 0:
            self.die(hero)
        else:
            # Отскакиваем от героя при получении урона
            dx = self.x - hero.x
            dy = self.y - hero.y
            distance = math.hypot(dx, dy)
            if distance != 0:
                dx /= distance
                dy /= distance
            self.x += dx * 20
            self.y += dy * 20
            self.rect.topleft = (self.x, self.y)  # Обновляем хитбокс
            
    def render(self, screen, camera_x, camera_y):
        """Отрисовка животного белым цветом."""
        pygame.draw.rect(
            screen,
            (255, 255, 255),  # Белый цвет
            pygame.Rect(self.x - camera_x, self.y - camera_y, 32, 32)
        )
    
    def die(self, hero):
        """Животное умирает, и герою восстанавливается HP."""
        print(f"{self.__class__.__name__} погибло.")
        self.hp = 0  # Убедимся, что HP не отрицательное
        self.active = 0  # Деактивируем животное
        if hero:
            hero.heal(2)  # Герой восстанавливает 2 HP

            
class SimpleNeuralNet:
    def __init__(self, input_size=4, hidden_size=6, output_size=2):
        self.weights = {
            'w1': np.random.randn(input_size, hidden_size),
            'b1': np.random.randn(hidden_size),
            'w2': np.random.randn(hidden_size, output_size),
            'b2': np.random.randn(output_size)
        }

    def forward(self, inputs):
        z1 = np.dot(inputs, self.weights['w1']) + self.weights['b1']
        a1 = np.tanh(z1)
        z2 = np.dot(a1, self.weights['w2']) + self.weights['b2']
        return np.tanh(z2)

                

class EnemyMelee(Entity):
    def __init__(self, hp, power, x, y, speed, protect, fov_radius, active):
        super().__init__(hp, power, x, y, speed, active)
        self.protect = protect
        self.fov_radius = fov_radius
        self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])  # Начальное направление
        self.movement_timer = random.randint(60, 120)  # Таймер для движения (сразу активируем движение)
        self.pause_timer = 0  # Пауза отключена в начале
        self.is_alive = True
        self.last_attack_time = 0  # Время последней атаки героя
        self.attack_cooldown = 1000  # Время между атаками (в миллисекундах)
        
        self.texture = pygame.image.load("gfx/enemy.png").convert_alpha()  # Загрузка текстуры
        self.texture = pygame.transform.scale(self.texture, (32, 32))  # Масштабируем до нужного размера

    def take_damage(self, amount):
        """Обработка получения урона."""
        self.hp -= amount
        print(f"{self.__class__.__name__} получил {amount} урона! Осталось HP: {self.hp}")
        if self.hp <= 0:
            self.is_alive = False
            print(f"{self.__class__.__name__} уничтожен!")

    def knockback(self, hero):
        """Отталкивание врага от героя."""
        dx, dy = self.x - hero.x, self.y - hero.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx, dy = dx / distance, dy / distance  # Нормализуем направление
            self.x += dx * 10  # Отталкиваем на небольшое расстояние
            self.y += dy * 10

    def update(self, hero, landscapes, hero_attacking=False):
        """Обновление поведения врага."""
        if not self.active:
            return

        # Вычисление расстояния до героя
        dx, dy = hero.x - self.x, hero.y - self.y
        distance_to_hero = math.hypot(dx, dy)

        # Если герой атакует и находится в радиусе атаки, враг получает урон
        if hero_attacking and distance_to_hero <= 50:
            self.take_damage(hero.power)
            self.knockback(hero)
            print(f"EnemyMelee получил урон! Осталось HP: {self.hp}")
            return

        # Если герой в поле зрения, двигаться к нему
        if distance_to_hero <= self.fov_radius:
            direction_x = dx / distance_to_hero
            direction_y = dy / distance_to_hero
            target_x = self.x + direction_x * self.speed
            target_y = self.y + direction_y * self.speed
            collision_detected = False

            # Проверка столкновений с горами
            for landscape in landscapes:
                clusters = getattr(landscape, 'mountains', []) + getattr(landscape, 'features', [])
                for cluster in clusters:
                    for block in cluster:
                        if pygame.Rect(target_x, target_y, 32, 32).colliderect(block):
                            collision_detected = True
                            print(f"Столкновение с горой: {block}")
                            break
                    if collision_detected:
                        break

            # Если нет столкновений, обновляем позицию
            if not collision_detected:
                self.x = target_x
                self.y = target_y
            else:
                # Случайное движение при столкновении
                self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])
                print("Враг изменил направление из-за столкновения.")
        else:
            # Случайное движение, если герой далеко
            self.random_movement(landscapes)

    def random_movement(self, landscapes):
        """Реализация случайного движения врага."""
        if self.pause_timer > 0:
            self.pause_timer -= 1
            return

        if self.movement_timer <= 0:
            self.pause_timer = random.randint(30, 120)  # Устанавливаем паузу
            self.movement_timer = random.randint(60, 120)  # Задаем новое время движения
            self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])
            return

        # Движение
        self.movement_timer -= 1
        target_x = self.x + self.direction[0] * self.speed
        target_y = self.y + self.direction[1] * self.speed
        collision_detected = False

        # Проверка столкновений
        for landscape in landscapes:
            clusters = getattr(landscape, 'mountains', []) + getattr(landscape, 'features', [])
            for cluster in clusters:
                for block in cluster:
                    if pygame.Rect(target_x, target_y, 32, 32).colliderect(block):
                        collision_detected = True
                        print(f"Случайное движение: враг столкнулся с {block}")
                        break
                if collision_detected:
                    break

        if not collision_detected:
            self.x = target_x
            self.y = target_y
        else:
            self.direction = np.array([random.choice([-1, 1]), random.choice([-1, 1])])



    def check_collision(self, new_x, new_y, landscapes):
        """Проверяет столкновения врага с препятствиями."""
        test_rect = pygame.Rect(new_x, new_y, 32, 32)
        for landscape in landscapes:
            for cluster in getattr(landscape, 'mountains', []):
                for segment in cluster:
                    if test_rect.colliderect(segment):
                        print(f"Враг столкнулся с {segment}.")
                        return True  # Обнаружено столкновение
        return False



    def draw(self, screen, camera_x, camera_y):
        """Отрисовка врага с текстурой, хитбоксом и полоской здоровья."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # Отрисовка текстуры врага, если она задана
        if hasattr(self, 'texture') and self.texture:
            screen.blit(self.texture, (screen_x, screen_y))
        else:
            # Если текстура отсутствует, рисуем врага как круг
            pygame.draw.circle(screen, (255, 0, 0), (int(screen_x + 16), int(screen_y + 16)), 20)

        # Отрисовка хитбокса врага
        pygame.draw.rect(screen, (255, 255, 255), (screen_x, screen_y, 32, 32), 1)

        # Полоска здоровья
        max_hp = getattr(self, 'max_hp', 50) 
        if self.hp < max_hp:  # Полоска появляется, только если HP меньше максимума
            health_bar_width = 32
            health_bar_height = 5
            health_ratio = max(self.hp, 0) / max_hp  # Убедитесь, что HP >= 0
            pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 8, health_bar_width, health_bar_height))  # Фон полоски
            pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 8, health_bar_width * health_ratio, health_bar_height))



class EnemyArcher(Entity):
    def __init__(self, hp, power, x, y, speed, protect, fov_radius, active):
        super().__init__(hp, power, x, y, speed, active)
        self.protect = protect
        self.fov_radius = fov_radius  # Поле зрения лучника
        self.shoot_delay = 1000  # Задержка между выстрелами (в миллисекундах)
        self.last_shot = pygame.time.get_ticks()
        self.bullets = []  # Список для пуль
        self.is_alive = True  # Враг жив

        # Создаем rect для столкновений
        self.rect = pygame.Rect(self.x - 16, self.y - 16, 32, 32)

    def update(self, hero, landscapes, hero_attacking=False):
        """Обновление состояния лучника."""
        if not self.is_alive:
            return

        # Вычисление расстояния до героя
        dx, dy = hero.x - self.x, hero.y - self.y
        distance_to_hero = math.hypot(dx, dy)

        # Если герой атакует, враг получает урон
        if hero_attacking and distance_to_hero <= 50:  # Радиус ближнего боя
            self.take_damage(hero.power)  # Получаем урон от героя
            self.knockback(hero)  # Отталкиваемся от героя
            print(f"EnemyArcher получил урон! Осталось HP: {self.hp}")
            return

        # Если герой в поле зрения, стреляем
        if distance_to_hero <= self.fov_radius:
            now = pygame.time.get_ticks()
            if now - self.last_shot >= self.shoot_delay:
                self.shoot(hero)
                self.last_shot = now

        # Обновляем все пули
        for bullet in self.bullets[:]:
            if not bullet.update(landscapes, hero):  # Проверяем обновление пули
                self.bullets.remove(bullet)  # Удаляем пулю, если она "умирает"

    def shoot(self, hero):
        """Стрельба в сторону героя."""
        dx, dy = hero.x - self.x, hero.y - self.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx, dy = dx / distance, dy / distance
            angle = math.atan2(dy, dx)
            bullet = Bullet(self.x + 16, self.y + 16, angle)  # Создаем пулю
            self.bullets.append(bullet)  # Добавляем пулю в список
            print("EnemyArcher выстрелил!")

    def take_damage(self, damage):
        """Обработка получения урона."""
        self.hp -= damage
        print(f"EnemyArcher получил {damage} урона. Осталось HP: {self.hp}")
        if self.hp <= 0:
            self.die()

    def die(self):
        """Логика смерти лучника."""
        self.is_alive = False
        print("EnemyArcher уничтожен!")

    def knockback(self, hero):
        """Отталкивание лучника от героя."""
        dx, dy = self.x - hero.x, self.y - hero.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx /= distance
            dy /= distance
            self.x += dx * 10
            self.y += dy * 10

    def draw(self, screen, camera_x, camera_y):
        """Отрисовка лучника и его пуль."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # Отрисовка самого лучника
        pygame.draw.circle(screen, (255, 165, 0), (int(screen_x + 16), int(screen_y + 16)), 20)

        # Отрисовка пуль
        for bullet in self.bullets:
            bullet.draw(screen, camera_x, camera_y)

class Bullet:
    def __init__(self, x, y, direction, radius=5, color=(255, 0, 0), speed=5, lifetime=3000):
        """Инициализация пули."""
        self.x = x
        self.y = y
        self.speed = speed  # Скорость пули
        self.direction = direction  # Угол направления (в радианах)
        self.creation_time = pygame.time.get_ticks()  # Время создания пули
        self.color = color  # Цвет пули
        self.radius = radius  # Радиус пули
        self.lifetime = lifetime  # Время жизни пули в миллисекундах

    def update(self, landscapes, hero):
        """Обновляет положение пули и проверяет столкновения."""
        # Проверяем, истекло ли время жизни пули
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            return False  # Пуля "умирает"

        # Обновляем координаты пули
        self.x += math.cos(self.direction) * self.speed
        self.y += math.sin(self.direction) * self.speed

        # Проверяем столкновение с героем
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32)
        bullet_rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2
        )
        if hero_rect.colliderect(bullet_rect):
            hero.take_damage(2)  # Герой получает 2 урона
            print("Герой получил урон от пули!")
            return False  # Пуля "умирает" при столкновении с героем

        # Проверяем столкновение с ландшафтом
        for landscape in landscapes:
            for cluster in getattr(landscape, 'mountains', []):
                for block in cluster:
                    if bullet_rect.colliderect(block):
                        print("Пуля столкнулась с препятствием и исчезает.")
                        return False  # Пуля "умирает" при столкновении с препятствием

        return True  # Пуля продолжает существовать

    def draw(self, screen, camera_x, camera_y):
        """Отрисовка пули на экране."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.radius)
        # Добавляем "светящийся" эффект вокруг пули
        pygame.draw.circle(screen, (255, 150, 150), (int(screen_x), int(screen_y)), self.radius + 2, 1)


class PlayerBullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.speed = 8
        self.direction = direction
        self.creation_time = pygame.time.get_ticks() 

    def update (self):
        if pygame.time.get_ticks() - self.creation_time > 800:
            return False

        if self.direction == 1: #лево
            self.x -= self.speed
        if self.direction == 2: #низ
            self.y += self.speed
        if self.direction == 3: #право
            self.x += self.speed
        if self.direction == 4: #верх
            self.y -= self.speed
        if self.direction == 12: #левониз
            self.x -= self.speed
            self.y += self.speed
        if self.direction == 32: #правониз
            self.x += self.speed
            self.y += self.speed
        if self.direction == 14: #левоверх
            self.x -= self.speed
            self.y -= self.speed
        if self.direction == 34: #правоверх
            self.x += self.speed
            self.y -= self.speed

        return True

class Cursor:
    def __init__(self):
        #self.image = pygame.image.load("gfx/cursor.png").convert_alpha()
        #self.rect = self.image.get_rect()
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.world_x = 0
        self.world_y = 0

    def update(self, camera_x, camera_y):
        """Обновление положения курсора"""
        # Получаем экранные координаты мыши
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Позиция курсора в игровом мире
        self.world_x = mouse_x + camera_x
        self.world_y = mouse_y + camera_y

        # Устанавливаем экранные координаты курсора для отрисовки
        self.rect.center = (mouse_x, mouse_y)

        # Отладка
        #print(f"Cursor screen: ({mouse_x}, {mouse_y}), world: ({self.world_x}, {self.world_y})")

    def draw(self, surface):
        """Отрисовка курсора"""
        #surface.blit(self.image, self.rect)
        pass


class Inventory:
    def __init__(self, x, y, cell_size, capacity):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.capacity = capacity
        self.items = [None] * capacity  # Пустые ячейки
        self.selected_index = None  # Выбранная ячейка
        self.mouse_offset = (0, 0)  # Смещение для отображения перетаскиваемого предмета
        self.selected_item = None  # Перетаскиваемый предмет

    def handle_key_press(self, key):
        """Обрабатывает нажатие клавиши для выбора ячейки."""
        if pygame.K_1 <= key <= pygame.K_9:  # Клавиши от 1 до 9
            index = key - pygame.K_1  # Преобразуем клавишу в индекс (0-8)
            if index < self.capacity:
                self.selected_index = index  # Устанавливаем выбранный индекс
                self.selected_item = self.items[index] if self.items[index] else None  # Обновляем выбранный предмет

                if self.selected_item:
                    print(f"Выбрана ячейка {index}, предмет: {self.selected_item}")
                else:
                    print(f"Выбрана ячейка {index}, но она пуста.")
            else:
                print(f"Индекс {index} выходит за пределы вместимости инвентаря!")
        else:
            print(f"Нажата неподдерживаемая клавиша: {key}")


    def render(self, screen):
        """Отрисовывает инвентарь на экране."""
        for index in range(self.capacity):
            x = self.x + 60 * index
            y = self.y
            color = (200, 200, 200)  # Обычная рамка

            if index == self.selected_index:
                color = (255, 255, 0)  # Подсветка выделенной ячейки

            pygame.draw.rect(screen, color, (x, y, self.cell_size, self.cell_size), 2)

            if self.items[index]:
                icon = self.get_item_icon(self.items[index])
                if icon:
                    screen.blit(icon, (x + 5, y + 5))

        # Если есть перетаскиваемый предмет, отрисовываем его на курсоре
        if self.selected_item:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            icon = self.get_item_icon(self.selected_item)
            if icon:
                scaled_icon = pygame.transform.scale(icon, (self.cell_size - 10, self.cell_size - 10))
                screen.blit(icon, (mouse_x + self.mouse_offset[0], mouse_y + self.mouse_offset[1]))

    def handle_click(self, mouse_x, mouse_y, dragging_item=None):
        """Обрабатывает взаимодействие с ячейками инвентаря."""
        for index in range(self.capacity):
            x = self.x + index * (self.cell_size + 10)
            y = self.y
            cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

            if cell_rect.collidepoint(mouse_x, mouse_y):
                if dragging_item:
                    # Перемещаем предмет в выбранную ячейку
                    if self.items[index] is None:
                        self.items[index] = dragging_item
                        dragging_item = None
                    else:
                        self.items[index], dragging_item = dragging_item, self.items[index]
                    return True, dragging_item
                else:
                    # Забираем предмет из ячейки
                    if self.items[index]:
                        dragging_item = self.items[index]
                        self.items[index] = None
                        return True, dragging_item
        return False, dragging_item
    
    def add_item(self, item_type):
        """Добавляет предмет в первую пустую ячейку инвентаря, игнорируя ячейки с инструментами."""
        tools = {"sword", "pickaxe", "gray_sword", "gray_pickaxe"}  # Список инструментов

        for index in range(self.capacity):
            # Если ячейка выходит за пределы текущего списка
            if index >= len(self.items):
                self.items.append(item_type)
                print(f"Предмет {item_type} добавлен в инвентарь, ячейка {index}.")
                return True

            # Если ячейка пустая, добавляем предмет
            if self.items[index] is None:
                self.items[index] = item_type
                print(f"Предмет {item_type} добавлен в инвентарь, ячейка {index}.")
                return True

            # Если ячейка занята инструментом, пропускаем её
            if self.items[index] in tools:
                continue

        print("Инвентарь полон или подходящая ячейка не найдена! Предмет не добавлен.")
        return False  # Указываем, что добавить предмет не удалось


    def remove_selected_item(self):
        """Удаляет выбранный предмет из инвентаря."""
        if self.selected_index is not None:
            self.items[self.selected_index] = None
            print(f"Предмет из ячейки {self.selected_index} удален.")

    def get_selected_item(self):
        """Возвращает предмет из выбранной ячейки."""
        if self.selected_index is not None and self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def get_item_icon(self, item_type):
        """Заглушка для получения иконки предмета."""
        if item_type == "brown_mountain_block":
            return pygame.image.load("gfx/mount.png").convert_alpha()
        elif item_type == "pickaxe":
            return pygame.image.load("gfx/pickaxe.png").convert_alpha()
        elif item_type == "sword":
            return pygame.image.load("gfx/sword.png").convert_alpha()
        elif item_type == "gray_mountain_block":
            return pygame.image.load("gfx/gray_block.png").convert_alpha()
        elif item_type == "gray_sword":
            return pygame.image.load("gfx/gray_sword.png").convert_alpha()
        elif item_type == "gray_pickaxe":
            return pygame.image.load("gfx/gray_pickaxe.png").convert_alpha()
        elif item_type == "purple_mountain_block":
            return pygame.image.load("gfx/purple_block.png").convert_alpha()
        elif item_type == "final_stick":
            return pygame.image.load("gfx/final_stick.png").convert_alpha()
        return None
    
    def drop_selected_item(self):
        """Удаляет выбранный предмет из инвентаря и возвращает его тип."""
        if self.selected_index is not None:
            dropped_item = self.items[self.selected_index]
            if dropped_item:
                print(f"Выкинут предмет: {dropped_item} из ячейки {self.selected_index}")
                self.items[self.selected_index] = None  # Убираем предмет из инвентаря
                return dropped_item
        print("Нет предмета для выбрасывания.")
        return None
    
    
class DroppedItem:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.item_type = item_type
        self.rect = pygame.Rect(x, y, 16, 16)  # Маленький размер для иконки

    def draw(self, screen, camera_x, camera_y):
        """Отрисовка предмета на экране."""
        if self.item_type == "brown_mountain_block":
            color = (139, 69, 19)  # Коричневый
        elif self.item_type == "gray_mountain_block":
            color = (128, 128, 128)  # Серый
        elif self.item_type == "purple_mountain_block":
            color = (75, 0, 130)  # Темно-фиолетовый
        elif self.item_type == "sword":
            color = (255, 0, 0)  # Красный для меча
        elif self.item_type == "pickaxe":
            color = (0, 0, 255)  # Синий для кирки
        else:
            color = (255, 255, 255)  # Белый для остальных
        pygame.draw.rect(screen, color, self.rect.move(-camera_x, -camera_y))

class CraftingTable:
    def __init__(self, x, y, cell_size):
        self.x = x  # Позиция верстака по оси X
        self.y = y  # Позиция верстака по оси Y
        self.cell_size = cell_size  # Размер ячеек
        self.items = [None] * 10  # 10 ячеек для крафта, изначально пустые
        self.selected_item = None  # Выбранный предмет, изначально None
        self.selected_index = None  # Индекс выбранной ячейки

    def handle_click(self, mouse_x, mouse_y, dragging_item=None):
        """Обрабатывает взаимодействие с ячейками верстака."""
        for index in range(10):  # У верстака теперь 10 ячеек
            col = index % 3
            row = index // 3
            x = self.x + (self.cell_size + 10) * col
            y = self.y + (self.cell_size + 10) * row
            cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

            if cell_rect.collidepoint(mouse_x, mouse_y):  # Проверяем попадание мыши
                if dragging_item:  # Если перетаскиваемый предмет есть
                    if self.items[index] is None:  # Если ячейка пустая
                        self.items[index] = dragging_item
                        dragging_item = None
                    else:  # Меняем местами предметы
                        self.items[index], dragging_item = dragging_item, self.items[index]
                    return True, dragging_item
                else:  # Если предмет не перетаскивается, выбираем предмет из ячейки
                    if self.items[index]:
                        dragging_item = self.items[index]
                        self.items[index] = None
                        return True, dragging_item
        return False, dragging_item

    def add_item(self, item):
        """Добавляет предмет в первую пустую ячейку верстака."""
        for index in range(len(self.items)):
            if self.items[index] is None:  # Если ячейка пустая
                self.items[index] = item
                print(f"Добавлен предмет {item} в ячейку верстака {index}.")
                return
        print("Верстак полон!")

    def remove_selected_item(self):
        """Удаляет выбранный предмет из верстака."""
        if self.selected_item in self.items:
            index = self.items.index(self.selected_item)
            self.items[index] = None
            print(f"Предмет {self.selected_item} удален из верстака.")
            self.selected_item = None

    def render(self, screen, get_icon):
        """Отрисовка верстака на экране."""
        for index in range(10):  # У верстака теперь 10 ячеек
            col = index % 3
            row = index // 3
            x = self.x + (self.cell_size + 10) * col
            y = self.y + (self.cell_size + 10) * row
            pygame.draw.rect(screen, (200, 200, 200), (x, y, self.cell_size, self.cell_size), 2)  # Рамка ячейки

            # Если в ячейке есть предмет, отрисовываем его иконку
            if self.items[index]:
                icon = get_icon(self.items[index])
                if icon:
                    screen.blit(icon, (x + 5, y + 5))  # С отступом, чтобы иконка смотрелась лучше

    def get_item_icon(self, item_type):
        """Получает иконку предмета по его типу."""
        if item_type == "brown_mountain_block":
            return pygame.image.load("gfx/brick.png").convert_alpha()
        elif item_type == "pickaxe":
            return pygame.image.load("gfx/pickaxe.png").convert_alpha()
        return None

    def can_craft(self):
        """Проверяет возможность крафта предметов."""
        t_pattern_pickaxe = [1, 4, 7, 3, 5]  # Индексы для формы T (кирка)
        sword_pattern = [1, 4, 3, 5]  # Индексы для формы меча
        final_stick_pattern = [1, 4, 7]  # Индексы для формы финальной палки


        # Проверка формы для кирки из коричневых блоков
        pickaxe_items_brown = [self.items[i] for i in t_pattern_pickaxe]
        is_t_shape_pickaxe_brown = all(item == "brown_mountain_block" for item in pickaxe_items_brown)

        # Проверка формы для кирки из серых блоков
        pickaxe_items_gray = [self.items[i] for i in t_pattern_pickaxe]
        is_t_shape_pickaxe_gray = all(item == "gray_mountain_block" for item in pickaxe_items_gray)

        # Проверка формы для меча из коричневых блоков
        sword_items_brown = [self.items[i] for i in sword_pattern]
        is_t_shape_sword_brown = all(item == "brown_mountain_block" for item in sword_items_brown)

        # Проверка формы для меча из серых блоков
        sword_items_gray = [self.items[i] for i in sword_pattern]
        is_t_shape_sword_gray = all(item == "gray_mountain_block" for item in sword_items_gray)
        
        # Проверка формы для финальной палки
        final_stick_items = [self.items[i] for i in final_stick_pattern]
        is_final_stick = all(item == "purple_mountain_block" for item in final_stick_items)

        # Логика определения типа крафта
        if is_t_shape_pickaxe_brown:
            print("Форма T для кирки из коричневых блоков собрана, можно крафтить!")
            return "pickaxe"
        elif is_t_shape_sword_brown:
            print("Форма для меча из коричневых блоков собрана, можно крафтить!")
            return "sword"
        elif is_t_shape_pickaxe_gray:
            print("Форма для меча из коричневых блоков собрана, можно крафтить!")
            return "sword"
        elif is_t_shape_sword_gray:
            print("Форма для кирки из серых блоков собрана, можно крафтить!")
            return "gray_sword"
        elif is_final_stick:
            print("Форма для финальной палки собрана, можно крафтить!")
            return "final_stick"
        else:
            print("Форма не собрана.")
            print(f"Текущие предметы: {self.items}")
            return False

    def craft(self):
        """Создает предмет на основе расположения в верстаке."""
        if self.can_craft():
            crafted_item = None
            # Удаляем использованные предметы и задаем созданный предмет
            if all(self.items[i] == "brown_mountain_block" for i in [1, 4, 7, 3, 5]):
                for i in [1, 4, 7, 3, 5]:
                    self.items[i] = None
                crafted_item = "pickaxe"

            elif all(self.items[i] == "gray_mountain_block" for i in [1, 4, 7, 3, 5]):
                for i in [1, 4, 7, 3, 5]:
                    self.items[i] = None
                crafted_item = "gray_pickaxe"

            elif all(self.items[i] == "brown_mountain_block" for i in [1, 4, 3, 5]):
                for i in [1, 4, 3, 5]:
                    self.items[i] = None
                crafted_item = "sword"

            elif all(self.items[i] == "gray_mountain_block" for i in [1, 4, 3, 5]):
                for i in [1, 4, 3, 5]:
                    self.items[i] = None
                crafted_item = "gray_sword"

            elif all(self.items[i] == "purple_mountain_block" for i in [1, 4, 7]):
                for i in [1, 4, 7]:
                    self.items[i] = None
                crafted_item = "final_stick"

            if crafted_item:
                print(f"Крафт завершен! Создан предмет: {crafted_item}.")
                return crafted_item  # Возвращаем правильный тип созданного предмета

        print("Крафт невозможен! Проверьте расположение блоков.")
        return None

    
    
class SpawnManager:
    def __init__(self, world_width, world_height, dark_biome):
        self.world_width = world_width
        self.world_height = world_height
        self.dark_biome = dark_biome
        self.initial_enemy_count = 0
        self.enemies_initialized = False
        self.respawn_cooldown = 5000  # 5 секунд кулдаун между респавнами
        self.last_respawn_time = pygame.time.get_ticks()

    def initialize_counts(self, enemy_list):
        """Инициализирует начальное количество врагов"""
        if not self.enemies_initialized:
            self.initial_enemy_count = len([enemy for enemy in enemy_list if enemy.active and enemy.hp > 0])
            self.enemies_initialized = True
            print(f"[SpawnManager] Установлено начальное количество врагов: {self.initial_enemy_count}")

    def get_random_spawn_position(self):
        """Получает случайную позицию для спавна, избегая темный биом"""
        for _ in range(10):  # До 10 попыток найти позицию
            x = random.randint(0, self.world_width - 64)
            y = random.randint(0, self.world_height - 64)
            if not self.dark_biome.is_rect_in_biome(pygame.Rect(x, y, 64, 64)):
                return x, y
        return None, None  # Если позиция не найдена

    def spawn_enemy(self):
        """Создает нового врага случайного типа на случайной позиции"""
        x, y = self.get_random_spawn_position()
        if x is None or y is None:
            return None
        enemy_type = random.choice(["melee", "archer"])
        if enemy_type == "melee":
            return EnemyMelee(hp=100, power=10, x=x, y=y, speed=2, protect=5, fov_radius=200, active=1)
        else:
            return EnemyArcher(hp=70, power=15, x=x, y=y, speed=1.5, protect=3, fov_radius=300, active=1)

    def update(self, enemy_list):
        """Проверяет и спавнит врагов при необходимости"""
        current_time = pygame.time.get_ticks()
        active_enemies = len([enemy for enemy in enemy_list if enemy.active and enemy.hp > 0])

        if current_time - self.last_respawn_time >= self.respawn_cooldown and active_enemies < self.initial_enemy_count:
            new_enemy = self.spawn_enemy()
            if new_enemy:
                enemy_list.append(new_enemy)
                print(f"[SpawnManager] Заспавнен новый враг на ({new_enemy.x}, {new_enemy.y}).")
            self.last_respawn_time = current_time
    
    
class AnimalSpawnManager:
    def __init__(self, world_width, world_height, dark_biome):
        self.world_width = world_width
        self.world_height = world_height
        self.dark_biome = dark_biome
        self.initial_animal_count = 0
        self.animals_initialized = False
        self.respawn_cooldown = 5000  # Кулдаун между респавнами животных (7 секунд)
        self.last_respawn_time = pygame.time.get_ticks()

    def initialize_counts(self, animal_list):
        """Инициализирует начальное количество животных"""
        if not self.animals_initialized:
            # Убедимся, что все животные активны и их здоровье > 0
            self.initial_animal_count = len([animal for animal in animal_list if getattr(animal, "active", 1) and getattr(animal, "hp", 1) > 0])
            self.enemies_initialized = True
            print(f"[AnimalSpawnManager] Установлено начальное количество животных: {self.initial_animal_count}")


    def get_random_spawn_position(self):
        """Получает случайную позицию для спавна, избегая темный биом"""
        for _ in range(10):  # До 10 попыток найти позицию
            x = random.randint(0, self.world_width - 64)
            y = random.randint(0, self.world_height - 64)
            if not self.dark_biome.is_rect_in_biome(pygame.Rect(x, y, 64, 64)):
                return x, y
        return None, None  # Если позиция не найдена

    def spawn_animal(self):
        """Создает новое животное на случайной позиции"""
        x, y = self.get_random_spawn_position()
        if x is None or y is None:
            return None
        return Animal(hp=50, x=x, y=y, speed=random.uniform(1.0, 2.0), active=1)

    def update(self, animal_list):
        """Проверяет и спавнит животных при необходимости"""
        current_time = pygame.time.get_ticks()
        active_animals = len([animal for animal in animal_list if animal.active and animal.hp > 0])

        if current_time - self.last_respawn_time >= self.respawn_cooldown and active_animals < self.initial_animal_count:
            new_animal = self.spawn_animal()
            if new_animal:
                animal_list.append(new_animal)
                print(f"[AnimalSpawnManager] Заспавнено новое животное на ({new_animal.x}, {new_animal.y}).")
            self.last_respawn_time = current_time
            
            
class FinalBoss(Entity):
    def __init__(self, hp, power, x, y, speed, size_multiplier=2):
        super().__init__(hp, power, x, y, speed, active=1)
        self.size_multiplier = size_multiplier  # Размер босса (в 2 раза больше героя)
        self.width = 64 * size_multiplier  # Ширина босса
        self.height = 64 * size_multiplier  # Высота босса
        self.max_hp = hp  # Для расчета полосы здоровья
        self.teleport_cooldown = 3000  # 3 секунды
        self.last_teleport_time = pygame.time.get_ticks()
        self.shoot_cooldown = 1500  # 1.5 секунды
        self.last_shot_time = pygame.time.get_ticks()
        self.target_x = x
        self.target_y = y
        self.bullet = None
        self.bullets = []  # Список для нескольких пуль
        self.is_alive = True
        self.knockback_distance = 192  # Откидывание героя на длину 3-х героев
        self.attack_phase = 0  # Счетчик атак 0
        self.phase_change_cooldown = 10000  # 10 Кулдаун между фазами
        self.last_phase_change = pygame.time.get_ticks()
        self.chase_radius = 500  # Радиус, в котором босс начинает преследовать героя
        self.attack_distance = 50  # Дистанция, с которой он может атаковать

    def chase_hero(self, hero, obstacles):
        """Преследование героя."""
        dx, dy = hero.x - self.x, hero.y - self.y
        distance = math.hypot(dx, dy)

        if distance <= self.chase_radius:  # Если герой в радиусе преследования
            if distance > self.attack_distance:  # Если герой не в радиусе атаки
                # Нормализация вектора движения
                dx, dy = dx / distance, dy / distance
                new_x = self.x + dx * self.speed
                new_y = self.y + dy * self.speed

                # Проверяем столкновения с препятствиями
                new_rect = pygame.Rect(new_x, new_y, self.width, self.height)
                if not any(
                    isinstance(segment, pygame.Rect) and new_rect.colliderect(segment)
                    for cluster in obstacles for segment in cluster
                ):
                    self.x = new_x
                    self.y = new_y



    def teleport(self, hero):
        """Телепортация босса к случайной точке или обратно к герою."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_teleport_time >= self.teleport_cooldown:
            if random.choice([True, False]):  # 50% шанс телепортации к герою или вдаль
                self.x = hero.x + random.randint(-200, 200)
                self.y = hero.y + random.randint(-200, 200)
                print("Босс телепортировался рядом с героем!")
            else:
                self.x = random.randint(0, 10000)  # Допустим, размеры карты
                self.y = random.randint(0, 10000)
                print("Босс телепортировался вдаль!")
            self.last_teleport_time = current_time

    def shoot(self, hero):
        """Босс стреляет пулями в зависимости от фазы."""
        current_time = pygame.time.get_ticks()
        
        # Смена фазы атаки
        if current_time - self.last_phase_change >= self.phase_change_cooldown:
            self.attack_phase = 1 - self.attack_phase  # Переключаем между 0 и 1
            self.last_phase_change = current_time
            print(f"Босс меняет фазу атаки на {self.attack_phase}!")

        if current_time - self.last_shot_time >= self.shoot_cooldown:
            if self.attack_phase == 0:
                # Обычная атака - стрельба в героя
                dx, dy = hero.x - self.x, hero.y - self.y
                angle = math.atan2(dy, dx)
                bullet = BossBullet(
                    self.x + self.width // 2,
                    self.y + self.height // 2,
                    angle
                )
                self.bullets.append(bullet)
            else:
                # Круговая атака - стрельба во все стороны
                for i in range(8):  # 8 пуль в разных направлениях
                    angle = (2 * math.pi * i) / 8
                    bullet = BossBullet(
                        self.x + self.width // 2,
                        self.y + self.height // 2,
                        angle,
                        speed=5  # Немного медленнее для баланса
                    )
                    self.bullets.append(bullet)
            
            self.last_shot_time = current_time

    def draw(self, screen, camera_x, camera_y):
        """Отрисовка босса и его полосы здоровья."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # Отрисовываем босса
        pygame.draw.rect(screen, (128, 0, 128), (screen_x, screen_y, self.width, self.height))

        # Полоса здоровья
        health_bar_width = self.width
        health_bar_height = 10
        health_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y - 15, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 15, health_bar_width * health_ratio, health_bar_height))

        # Отрисовка пуль
        for bullet in self.bullets:
            bullet.draw(screen, camera_x, camera_y)

    def take_damage(self, damage):
        """Получение урона боссом."""
        self.hp -= damage
        print(f"Босс получил {damage} урона. Осталось HP: {self.hp}")
        if self.hp <= 0:
            self.is_alive = False
            print("Финальный босс повержен!")

    def knockback_hero(self, hero):
        """Отталкивание героя при ударе."""
        dx, dy = hero.x - self.x, hero.y - self.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            dx /= distance
            dy /= distance
            hero.x += dx * self.knockback_distance
            hero.y += dy * self.knockback_distance

    def update(self, hero, obstacles, gameplay):
        """Обновление состояния босса."""
        self.teleport(hero)
        self.shoot(hero)
        self.chase_hero(hero, obstacles)
        
        # Обновляем все пули и удаляем те, которые нужно удалить
        self.bullets = [bullet for bullet in self.bullets if bullet.update(hero)]

        # Проверяем столкновение с героем
        if pygame.Rect(self.x, self.y, self.width, self.height).colliderect(hero.rect):
            hero.take_damage(9)
            self.knockback_hero(hero)
            print("Герой ударен боссом! -9 HP")
            
    def die(self):
        """Действия при смерти босса."""
        self.is_alive = False
        print("Финальный босс уничтожен!")



class BossBullet:
    def __init__(self, x, y, angle, speed=7, radius=8, color=(128, 0, 128)):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.radius = radius
        self.color = color
        self.creation_time = pygame.time.get_ticks()
        self.lifetime = 5000  # 5 секунд жизни для пуль босса
        self.damage = 15  # Урон от пули босса

    def update(self, hero):
        """Обновление позиции пули."""
        # Проверяем время жизни пули
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            return False

        # Обновляем позицию
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Проверяем попадание в героя
        hero_rect = pygame.Rect(hero.x, hero.y, 32, 32)
        bullet_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                                self.radius * 2, self.radius * 2)
        
        if hero_rect.colliderect(bullet_rect):
            hero.take_damage(self.damage)
            print(f"Герой получил {self.damage} урона от пули босса!")
            return False

        return True

    def draw(self, screen, camera_x, camera_y):
        """Отрисовка пули босса."""
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), self.radius)
        # Добавляем светящийся эффект
        pygame.draw.circle(screen, (200, 100, 200), (screen_x, screen_y), self.radius - 2)