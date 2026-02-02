import arcade
import math
from arcade.future.light import Light, LightLayer
import random
from arcade.particles import FadeParticle, Emitter, EmitMaintainCount
import os

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
WINDOW_TITLE = "Game"

# 🔥 КОНСТАНТЫ ОТСЧЕТА
COUNTDOWN_TIME = 5.0

# 🔥 КОНСТАНТЫ ВРАГОВ
ENEMY_TYPES = ['BASIC', 'TANK', 'SHOOTER', 'FAST']

# Базовые враги (уже есть)
ENEMY_SPEED = 120
ENEMY_DAMAGE = 10
ENEMY_HEALTH = 30

# Танк
TANK_HEALTH = 100
TANK_SPEED = 60
TANK_DAMAGE = 20
TANK_SCALE = 4.0

# Стрелок
SHOOTER_HEALTH = 40
SHOOTER_SPEED = 100
SHOOTER_DAMAGE = 8
SHOOTER_SCALE = 2.5
SHOOTER_RANGE = 300  # Дистанция стрельбы
SHOOTER_COOLDOWN = 2.0  # Перезарядка стрельбы

# Быстрый
FAST_HEALTH = 20
FAST_SPEED = 250
FAST_DAMAGE = 5
FAST_SCALE = 3

# Босс
BOSS_HEALTH = 500
BOSS_SPEED = 80
BOSS_DAMAGE = 30
BOSS_SCALE = 6.0
BOSS_RANGE = 400
BOSS_COOLDOWN = 1.5
BOSS_SPAWN_WAVE = 5  # Каждую 5-ю волну появляется босс

# Опыт за разных врагов
XP_BASIC = 10
XP_TANK = 25
XP_SHOOTER = 15
XP_FAST = 8
XP_BOSS = 100

# Другие константы
SPAWN_INTERVAL = 8.0
ENEMIES_PER_WAVE = 3
XP_PER_LEVEL = 100
SKILL_POINTS_PER_LEVEL = 1
MAX_SKILL_LEVEL = 20

# Скорость анимации (кадры в секунду)
ANIMATION_FPS_BASIC = 2.0
ANIMATION_FPS_TANK = 2.0
ANIMATION_FPS_SHOOTER = 2.0
ANIMATION_FPS_FAST = 1.0
ANIMATION_FPS_BOSS = 1.0

# Текстуры для частиц
SPARK_TEX = [
    arcade.make_soft_circle_texture(10, arcade.color.WHITE_SMOKE),
    arcade.make_soft_circle_texture(10, arcade.color.WHITE),
    arcade.make_soft_circle_texture(10, arcade.color.GHOST_WHITE),
]


def make_trail(attached_sprite, maintain=60):
    """Создаёт эмиттер частиц для следа"""
    emit = Emitter(
        center_xy=(attached_sprite.center_x, attached_sprite.center_y),
        emit_controller=EmitMaintainCount(maintain),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=random.choice(SPARK_TEX),
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 3),
            lifetime=random.uniform(0.35, 0.6),
            start_alpha=220,
            end_alpha=0,
            scale=random.uniform(0.5, 2),
        ),
    )
    emit._attached = attached_sprite
    return emit


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__("textures/player_up.png", scale=1.0)
        self.health = 100
        self.max_health = 100
        self.speed = 300
        self.direction = 'down'
        self.textures = {
            'up': arcade.load_texture("textures/player_up.png"),
            'down': arcade.load_texture("textures/player_down.png"),
            'left': arcade.load_texture("textures/player_left.png"),
            'right': arcade.load_texture("textures/player_right.png"),
        }
        self.texture = self.textures['down']
        self.trail = None
        self.light = None
        self.shoot_direction = (0, -1)

        # 🔥 СИСТЕМА ПРОКАЧКИ
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = XP_PER_LEVEL
        self.skill_points = 0

        # 🔥 ХАРАКТЕРИСТИКИ
        self.stats = {
            'health': {'base': 100, 'bonus': 0, 'cost': 1},
            'damage': {'base': 10, 'bonus': 0, 'cost': 1},
            'speed': {'base': 300, 'bonus': 0, 'cost': 1},
            'attack_radius': {'base': 30, 'bonus': 0, 'cost': 2},
            'reload_speed': {'base': 0.2, 'bonus': 0, 'cost': 2},
            'bullet_speed': {'base': 500, 'bonus': 0, 'cost': 1},
            'bullet_lifetime': {'base': 1.5, 'bonus': 0, 'cost': 2},
        }

    def update_direction(self, dx, dy):
        """Обновляет направление игрока и текстуру"""
        if dx == 0 and dy == 0:
            return

        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = 'right'
                self.shoot_direction = (1, 0)
            else:
                self.direction = 'left'
                self.shoot_direction = (-1, 0)
        else:
            if dy > 0:
                self.direction = 'up'
                self.shoot_direction = (0, 1)
            else:
                self.direction = 'down'
                self.shoot_direction = (0, -1)

        self.texture = self.textures[self.direction]

    def add_xp(self, amount):
        """Добавляет опыт игроку"""
        self.xp += amount
        print(f"🎯 +{amount} XP! Всего: {self.xp}/{self.xp_to_next_level}")

        while self.xp >= self.xp_to_next_level:
            self.level_up()

    def level_up(self):
        """Повышение уровня"""
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.skill_points += SKILL_POINTS_PER_LEVEL
        self.xp_to_next_level = int(XP_PER_LEVEL * (1.5 ** (self.level - 1)))

        self.max_health += 10
        self.health = min(self.health + 20, self.max_health)

        print(f"🎉 УРОВЕНЬ {self.level}!")
        print(f"   Очков навыков: {self.skill_points}")
        print(f"   Макс. здоровье: {self.max_health}")

    def upgrade_stat(self, stat_name):
        """Улучшает характеристику"""
        if self.skill_points <= 0:
            print("❌ Нет очков навыков!")
            return False

        if stat_name not in self.stats:
            print(f"❌ Характеристика '{stat_name}' не найдена!")
            return False

        stat = self.stats[stat_name]

        if stat['bonus'] >= MAX_SKILL_LEVEL:
            print(f"❌ {stat_name} достиг максимума!")
            return False

        if self.skill_points < stat['cost']:
            print(f"❌ Нужно {stat['cost']} очков, а есть {self.skill_points}")
            return False

        self.skill_points -= stat['cost']
        stat['bonus'] += 1
        self.apply_stat_bonus(stat_name)

        print(f"✅ {stat_name} улучшена до +{stat['bonus']}%")
        return True

    def apply_stat_bonus(self, stat_name):
        """Применяет бонус к характеристике"""
        stat = self.stats[stat_name]
        bonus_multiplier = 1 + (stat['bonus'] * 0.01)

        if stat_name == 'health':
            old_max = self.max_health
            self.max_health = int(stat['base'] * bonus_multiplier)
            health_percent = self.health / old_max if old_max > 0 else 1
            self.health = int(self.max_health * health_percent)

        elif stat_name == 'speed':
            self.speed = int(stat['base'] * bonus_multiplier)

    def get_stat_value(self, stat_name):
        """Возвращает текущее значение характеристики с бонусами"""
        if stat_name not in self.stats:
            return 0
        stat = self.stats[stat_name]
        return int(stat['base'] * (1 + stat['bonus'] * 0.01))

    def get_stat_percentage(self, stat_name):
        """Возвращает процент улучшения"""
        if stat_name not in self.stats:
            return 0
        return self.stats[stat_name]['bonus']


class EnemyBullet:
    """Пуля врага (стрелка и босса)"""

    def __init__(self, x, y, direction, damage=10, speed=400):
        self.x = x
        self.y = y
        self.radius = 4
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = 2.0
        self.should_remove = False

        try:
            self.sprite = arcade.Sprite("textures/arrow.png", scale=2)
            self.sprite.color = (255, 0, 0)  # Красный для вражеских пуль
        except:
            bullet_texture = arcade.make_soft_circle_texture(8, (255, 0, 0))
            self.sprite = arcade.Sprite(bullet_texture, scale=2)

        self.sprite.center_x = x
        self.sprite.center_y = y
        self.dx = direction[0] * self.speed
        self.dy = direction[1] * self.speed

        # Свет для пули
        self.light = Light(x, y, 30, (255, 50, 50), 'soft')

    def update(self, delta_time):
        self.x += self.dx * delta_time
        self.y += self.dy * delta_time
        self.lifetime -= delta_time

        self.sprite.center_x = self.x
        self.sprite.center_y = self.y

        if self.light:
            self.light.position = (self.x, self.y)

        if self.lifetime <= 0:
            self.should_remove = True

        return self.should_remove


class Enemy(arcade.Sprite):
    """Базовый класс для всех врагов с анимацией и текстурами"""

    # Кэш текстур для всех врагов
    _texture_cache = {}

    @classmethod
    def load_enemy_textures(cls, enemy_type):
        """Загружает текстуры для врага по типу"""
        if enemy_type in cls._texture_cache:
            return cls._texture_cache[enemy_type]

        type_lower = enemy_type.lower()
        textures = {
            'up': [],
            'down': [],
            'left': [],
            'right': []
        }

        # 🔥 ИСПРАВЛЕНИЕ: для FAST и BOSS - 1 кадр, для остальных - 2 кадра
        if enemy_type in ['FAST', 'BOSS']:
            frame_count = 1  # 🔥 1 кадр для быстрых и босса (статика)
        else:
            frame_count = 2  # 2 кадра для остальных (анимация)

        print(f"\n🔄 Загрузка текстур для: {enemy_type} (кадров: {frame_count})")

        # Создаем список всех возможных имен
        directions = ['up', 'down', 'left', 'right']

        for direction in directions:
            for frame in range(frame_count):
                # Пробуем 3 варианта имен
                names_to_try = [
                    # 1. Основной вариант: тип_направление_кадр
                    f"{type_lower}_{direction}_{frame}.png",
                    # 2. Сокращенный: первые 3 буквы типа
                    f"{type_lower[:3]}_{direction}_{frame}.png",
                    # 3. С приставкой enemy_
                    f"enemy_{type_lower}_{direction}_{frame}.png",
                    # 4. Без номера кадра (если только 1 кадр)
                    f"{type_lower}_{direction}.png",
                    f"{type_lower[:3]}_{direction}.png",
                    f"enemy_{type_lower}_{direction}.png",
                ]

                texture_loaded = False
                for name in names_to_try:
                    texture_path = f"textures/enemies/{name}"
                    try:
                        texture = arcade.load_texture(texture_path)
                        textures[direction].append(texture)
                        texture_loaded = True
                        print(f"✅ Загружено: {name}")
                        break
                    except:
                        continue

                # Если не нашли файл, создаем резервную текстуру
                if not texture_loaded:
                    color = cls._get_color_for_type(enemy_type)

                    # Разные размеры для разных врагов
                    sizes = {
                        'BASIC': 50,
                        'TANK': 60,
                        'SHOOTER': 40,
                        'FAST': 30,
                        'BOSS': 80
                    }

                    size = sizes.get(enemy_type, 50)
                    temp_texture = arcade.make_soft_square_texture(size, color)
                    textures[direction].append(temp_texture)
                    print(f"⚠️ Резервная: для {enemy_type}_{direction}_{frame}")

        cls._texture_cache[enemy_type] = textures
        return textures

    @staticmethod
    def _get_color_for_type(enemy_type):
        """Возвращает цвет для врага в зависимости от типа"""
        if enemy_type == 'BASIC':
            return arcade.color.RED
        elif enemy_type == 'TANK':
            return arcade.color.DARK_RED
        elif enemy_type == 'SHOOTER':
            return arcade.color.DARK_GREEN
        elif enemy_type == 'FAST':
            return arcade.color.ORANGE
        elif enemy_type == 'BOSS':
            return arcade.color.PURPLE
        else:
            return arcade.color.RED

    def __init__(self, x, y, player, enemy_type='BASIC'):
        # Загружаем текстуры
        self.enemy_type = enemy_type
        self.textures_dict = self.load_enemy_textures(enemy_type)

        # Инициализируем спрайт с первой текстурой
        super().__init__(self.textures_dict['down'][0], scale=1.0)

        self.center_x = x
        self.center_y = y
        self.player = player
        self.enemy_type = enemy_type

        # Устанавливаем характеристики в зависимости от типа
        self.set_stats_by_type()

        # Масштабируем в зависимости от типа
        if enemy_type == 'TANK':
            self.scale = TANK_SCALE
        elif enemy_type == 'SHOOTER':
            self.scale = SHOOTER_SCALE
        elif enemy_type == 'FAST':
            self.scale = FAST_SCALE
        elif enemy_type == 'BOSS':
            self.scale = BOSS_SCALE
        else:
            self.scale = 3.0

        # Направление и анимация
        self.direction = 'down'
        self.current_frame = 0
        self.animation_timer = 0

        # 🔥 ИСПРАВЛЕНИЕ: Скорость анимации из констант
        if enemy_type == 'BASIC':
            self.animation_fps = ANIMATION_FPS_BASIC
        elif enemy_type == 'TANK':
            self.animation_fps = ANIMATION_FPS_TANK
        elif enemy_type == 'SHOOTER':
            self.animation_fps = ANIMATION_FPS_SHOOTER
        elif enemy_type == 'FAST':
            self.animation_fps = ANIMATION_FPS_FAST
        elif enemy_type == 'BOSS':
            self.animation_fps = ANIMATION_FPS_BOSS
        else:
            self.animation_fps = 2.0  # По умолчанию

        self.attack_cooldown = 1.0
        self.time_since_attack = 0
        self.shoot_cooldown = SHOOTER_COOLDOWN if enemy_type in ['SHOOTER', 'BOSS'] else 0
        self.time_since_shot = 0
        self.radius = self.width / 2
        self.push_force = 50

        # Цвет света в зависимости от типа
        if enemy_type == 'BASIC':
            light_color = (255, 50, 50)  # Красный
        elif enemy_type == 'TANK':
            light_color = (200, 0, 0)  # Тёмно-красный
        elif enemy_type == 'SHOOTER':
            light_color = (0, 200, 0)  # Зелёный
        elif enemy_type == 'FAST':
            light_color = (255, 165, 0)  # Оранжевый
        elif enemy_type == 'BOSS':
            light_color = (150, 0, 150)  # Фиолетовый
        else:
            light_color = (255, 50, 50)

        self.light = Light(x, y, 80 if enemy_type != 'BOSS' else 120, light_color, 'soft')

        # Для стреляющих врагов
        if enemy_type in ['SHOOTER', 'BOSS']:
            self.can_shoot = True

    def set_stats_by_type(self):
        """Устанавливает характеристики в зависимости от типа врага"""
        if self.enemy_type == 'BASIC':
            self.health = ENEMY_HEALTH
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.xp_value = XP_BASIC
        elif self.enemy_type == 'TANK':
            self.health = TANK_HEALTH
            self.speed = TANK_SPEED
            self.damage = TANK_DAMAGE
            self.xp_value = XP_TANK
        elif self.enemy_type == 'SHOOTER':
            self.health = SHOOTER_HEALTH
            self.speed = SHOOTER_SPEED
            self.damage = SHOOTER_DAMAGE
            self.xp_value = XP_SHOOTER
        elif self.enemy_type == 'FAST':
            self.health = FAST_HEALTH
            self.speed = FAST_SPEED
            self.damage = FAST_DAMAGE
            self.xp_value = XP_FAST
        elif self.enemy_type == 'BOSS':
            self.health = BOSS_HEALTH
            self.speed = BOSS_SPEED
            self.damage = BOSS_DAMAGE
            self.xp_value = XP_BOSS
            # Босс имеет броню - уменьшает получаемый урон
            self.armor = 0.5  # 50% снижение урона
        else:
            self.health = ENEMY_HEALTH
            self.speed = ENEMY_SPEED
            self.damage = ENEMY_DAMAGE
            self.xp_value = XP_BASIC

    def update_animation(self, delta_time):
        """Обновляет анимацию врага"""
        # 🔥 ИСПРАВЛЕНИЕ: Если FPS = 1 (статика), не обновляем анимацию
        if self.animation_fps <= 0:
            return

        self.animation_timer += delta_time
        frame_duration = 1.0 / self.animation_fps

        if self.animation_timer >= frame_duration:
            self.animation_timer = 0
            frames = self.textures_dict[self.direction]
            if frames and len(frames) > 1:  # 🔥 Только если есть несколько кадров
                self.current_frame = (self.current_frame + 1) % len(frames)
                self.texture = frames[self.current_frame]

    def update_direction(self, dx, dy):
        """Обновляет направление врага в зависимости от движения"""
        if dx == 0 and dy == 0:
            return

        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = 'right'
            else:
                self.direction = 'left'
        else:
            if dy > 0:
                self.direction = 'up'
            else:
                self.direction = 'down'

        # Обновляем текстуру
        frames = self.textures_dict[self.direction]
        if frames:
            self.texture = frames[0]  # 🔥 Всегда берем первый кадр

    def die(self, game):
        """Враг умирает и дает опыт"""
        if hasattr(game, 'player'):
            game.player.add_xp(self.xp_value)

    def take_damage(self, damage):
        """Получение урона с учетом брони"""
        if self.enemy_type == 'BOSS':
            damage = int(damage * (1 - self.armor))
        self.health -= damage
        return damage

    def update(self, delta_time):
        # Обновляем анимацию
        self.update_animation(delta_time)

        self.time_since_attack += delta_time

        if self.enemy_type in ['SHOOTER', 'BOSS']:
            self.time_since_shot += delta_time

        if self.player and self.player.health > 0:
            dx = self.player.center_x - self.center_x
            dy = self.player.center_y - self.center_y
            dist = max(1, math.sqrt(dx * dx + dy * dy))

            # Обновляем направление
            self.update_direction(dx, dy)

            # ИИ в зависимости от типа
            if self.enemy_type == 'SHOOTER':
                # Стрелок держит дистанцию
                if dist > SHOOTER_RANGE:
                    # Подходит ближе если слишком далеко
                    self.change_x = (dx / dist) * self.speed * delta_time
                    self.change_y = (dy / dist) * self.speed * delta_time
                elif dist < SHOOTER_RANGE - 100:
                    # Отходит если слишком близко
                    self.change_x = (-dx / dist) * self.speed * delta_time
                    self.change_y = (-dy / dist) * self.speed * delta_time
                else:
                    # Стоит на месте для стрельбы
                    self.change_x = 0
                    self.change_y = 0
            else:
                # Все остальные преследуют
                self.change_x = (dx / dist) * self.speed * delta_time
                self.change_y = (dy / dist) * self.speed * delta_time

            self.center_x += self.change_x
            self.center_y += self.change_y

            # Ближняя атака
            player_distance = math.sqrt(
                (self.center_x - self.player.center_x) ** 2 +
                (self.center_y - self.player.center_y) ** 2
            )

            if player_distance < 40:  # Дистанция ближней атаки
                if self.time_since_attack >= self.attack_cooldown:
                    self.attack_player()
                    self.time_since_attack = 0

            # Стрельба для стрелка и босса
            if self.enemy_type in ['SHOOTER', 'BOSS']:
                shoot_range = SHOOTER_RANGE if self.enemy_type == 'SHOOTER' else BOSS_RANGE
                cooldown = SHOOTER_COOLDOWN if self.enemy_type == 'SHOOTER' else BOSS_COOLDOWN

                if dist <= shoot_range and self.time_since_shot >= cooldown:
                    self.shoot()
                    self.time_since_shot = 0

            # Обновляем позицию света
            if self.light:
                self.light.position = (self.center_x, self.center_y)

    def attack_player(self):
        """Нанесение урона игроку"""
        if self.player.health > 0:
            self.player.health -= self.damage
            print(f"⚔️ {self.enemy_type} нанес урон {self.damage}! Здоровье: {self.player.health}")

            if self.player.health <= 0:
                print("💀 Игрок погиб!")

    def shoot(self):
        """Стрельба для стрелка и босса"""
        # Эта функция должна быть переопределена в классе игры
        # Здесь мы только создаем пулю, а обработка будет в основном классе
        pass


class Bullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.radius = 5
        self.direction = direction
        self.speed = 500
        self.lifetime = 1.5
        self.should_remove = False

        try:
            self.sprite = arcade.Sprite("textures/bullet.png", scale=3)
        except:
            bullet_texture = arcade.make_soft_circle_texture(10, arcade.color.YELLOW)
            self.sprite = arcade.Sprite(bullet_texture, scale=1)

        self.sprite.center_x = x
        self.sprite.center_y = y
        self.dx = direction[0] * self.speed
        self.dy = direction[1] * self.speed
        self.trail = make_trail(self.sprite, maintain=30)
        self.light = Light(x, y, 50, arcade.color.WHITE, 'soft')

    def update(self, delta_time):
        self.x += self.dx * delta_time
        self.y += self.dy * delta_time
        self.lifetime -= delta_time

        self.sprite.center_x = self.x
        self.sprite.center_y = self.y
        self.trail.center_x = self.x
        self.trail.center_y = self.y

        if self.light:
            self.light.position = (self.x, self.y)

        if self.lifetime <= 0:
            self.should_remove = True

        return self.should_remove


class Level:
    def __init__(self, map_name):
        try:
            self.tile_map = arcade.load_tilemap(map_name, scaling=1)
            self.wall_list = self.tile_map.sprite_lists.get("walls", arcade.SpriteList())
            self.fon_list = self.tile_map.sprite_lists.get("fon", arcade.SpriteList())
            self.collision_list = self.tile_map.sprite_lists.get("collision", arcade.SpriteList())

            self.background = arcade.SpriteList()
            for sprite in self.fon_list:
                self.background.append(sprite)

            self.walls = arcade.SpriteList()
            for sprite in self.wall_list:
                self.walls.append(sprite)

            self.collision_sprites = arcade.SpriteList()
            for sprite in self.collision_list:
                self.collision_sprites.append(sprite)

            print(f"Карта '{map_name}' успешно загружена")

        except Exception as e:
            print(f"Ошибка загрузки карты {map_name}: {e}")
            raise


class Inventory:
    def __init__(self, player):
        self.player = player
        self.visible = False
        self.grid_positions = [
            (150, 300), (300, 300), (450, 300),
            (150, 200), (300, 200), (450, 200),
            (150, 100), (300, 100), (450, 100),
        ]
        self.stat_names = [
            'health', 'damage', 'speed',
            'attack_radius', 'reload_speed', 'bullet_speed',
            'bullet_lifetime'
        ]
        self.stat_display_names = {
            'health': '❤️ Здоровье',
            'damage': '⚔️ Урон',
            'speed': '⚡ Скорость',
            'attack_radius': '🎯 Радиус',
            'reload_speed': '🔫 Перезарядка',
            'bullet_speed': '💨 Скорость пуль',
            'bullet_lifetime': '⏱️ Дальность'
        }

    def toggle(self):
        self.visible = not self.visible
        print(f"📦 Инвентарь: {'открыт' if self.visible else 'закрыт'}")

    def draw(self):
        if not self.visible:
            return

        inventory_top = SCREEN_HEIGHT - 50
        inventory_bottom = 50

        arcade.draw_lrbt_rectangle_filled(
            left=50,
            right=SCREEN_WIDTH - 50,
            top=inventory_top,
            bottom=inventory_bottom,
            color=(30, 30, 40, 230)
        )

        arcade.draw_lrbt_rectangle_outline(
            left=50,
            right=SCREEN_WIDTH - 50,
            top=inventory_top,
            bottom=inventory_bottom,
            color=arcade.color.GOLD,
            border_width=3
        )

        arcade.draw_text(
            "🎮 ПРОКАЧКА ХАРАКТЕРИСТИК",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80,
            arcade.color.GOLD, 24,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Уровень: {self.player.level} | Опыт: {self.player.xp}/{self.player.xp_to_next_level}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120,
            arcade.color.WHITE, 18,
            anchor_x="center"
        )

        arcade.draw_text(
            f"🎯 Очков навыков: {self.player.skill_points}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,
            arcade.color.CYAN, 22,
            anchor_x="center",
            bold=True
        )

        for i, (pos_x, pos_y) in enumerate(self.grid_positions):
            if i < len(self.stat_names):
                stat_name = self.stat_names[i]
                self.draw_stat_card(stat_name, pos_x, pos_y)

    def draw_stat_card(self, stat_name, x, y):
        stat = self.player.stats.get(stat_name, {})
        bonus = stat.get('bonus', 0)
        cost = stat.get('cost', 1)
        display_name = self.stat_display_names.get(stat_name, stat_name)

        card_height = 80
        half_height = card_height // 2
        card_top = y + half_height
        card_bottom = y - half_height

        if card_bottom >= card_top:
            card_bottom, card_top = card_top, card_bottom

        color = arcade.color.DARK_BLUE_GRAY if bonus < MAX_SKILL_LEVEL else arcade.color.DARK_GREEN
        arcade.draw_lrbt_rectangle_filled(
            left=x - 70,
            right=x + 70,
            top=card_top,
            bottom=card_bottom,
            color=color
        )

        arcade.draw_lrbt_rectangle_outline(
            left=x - 70,
            right=x + 70,
            top=card_top,
            bottom=card_bottom,
            color=arcade.color.WHITE,
            border_width=2
        )

        arcade.draw_text(
            display_name,
            x, y + 20,
            arcade.color.WHITE, 14,
            anchor_x="center",
            anchor_y="center"
        )

        arcade.draw_text(
            f"+{bonus}%",
            x, y,
            arcade.color.YELLOW, 18,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        button_height = 20
        button_top = card_bottom + button_height + 5
        button_bottom = card_bottom + 5

        if button_bottom >= button_top:
            button_bottom, button_top = button_top, button_bottom

        if bonus < MAX_SKILL_LEVEL and self.player.skill_points >= cost:
            button_color = arcade.color.GREEN
            text_color = arcade.color.WHITE
            button_text = f"+ ({cost})"
        else:
            button_color = arcade.color.DARK_GRAY
            text_color = arcade.color.GRAY
            button_text = "МАКС" if bonus >= MAX_SKILL_LEVEL else f"Нужно {cost}"

        arcade.draw_lrbt_rectangle_filled(
            left=x - 60,
            right=x + 60,
            top=button_top,
            bottom=button_bottom,
            color=button_color
        )

        arcade.draw_text(
            button_text,
            x, (button_bottom + button_top) / 2,
            text_color, 12,
            anchor_x="center",
            anchor_y="center"
        )

    def check_click(self, x, y):
        if not self.visible:
            return False

        for i, (pos_x, pos_y) in enumerate(self.grid_positions):
            if i < len(self.stat_names):
                card_height = 80
                half_height = card_height // 2
                card_bottom = pos_y - half_height
                button_height = 20
                button_top = card_bottom + button_height + 5
                button_bottom = card_bottom + 5

                if (pos_x - 60 <= x <= pos_x + 60 and
                        button_bottom <= y <= button_top):
                    stat_name = self.stat_names[i]
                    if self.player.upgrade_stat(stat_name):
                        print(f"🔼 Улучшена {stat_name}")
                    return True
        return False


class GameCamera:
    def __init__(self):
        self.camera = arcade.Camera2D()
        self.position = (0, 0)

    def center(self, target_x, target_y):
        self.position = (target_x, target_y)
        self.camera.position = self.position

    def use(self):
        self.camera.use()


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=False)

        self.game_camera = GameCamera()
        self.gui_camera = arcade.Camera2D()

        self.camera_left_bound = 0
        self.camera_right_bound = 0
        self.camera_bottom_bound = 0
        self.camera_top_bound = 0

        self.enemy_lights = []
        self.background_color = arcade.color.BLACK

        self.light_layer = LightLayer(width, height)
        self.light_layer.set_background_color(arcade.color.BLACK)

        self.enemies = arcade.SpriteList()
        self.enemy_bullets = []  # 🔥 Пули врагов
        self.enemy_bullet_sprites = arcade.SpriteList()

        self.player = Player()
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)

        self.level = None
        self.physics_engine = None

        self.bullets = []
        self.bullet_sprites = arcade.SpriteList()
        self.emitters = []
        self.keys_pressed = set()

        self.can_shoot = True
        self.shoot_cooldown = 0.2

        # 🔥 СИСТЕМА ВРАГОВ
        self.countdown_time = COUNTDOWN_TIME
        self.countdown_active = True
        self.countdown_text = ""
        self.game_started = False
        self.spawn_timer = 0
        self.spawn_interval = SPAWN_INTERVAL
        self.base_enemies_per_wave = ENEMIES_PER_WAVE
        self.enemies_per_wave_increase = 1
        self.wave_number = 1
        self.max_enemies = 25  # Увеличил из-за разных типов
        self.wave_cleared = True
        self.current_wave_enemies = 0

        # 🔥 ИНФОРМАЦИЯ О ВРАГАХ
        self.enemy_info = {
            'BASIC': {'count': 0, 'icon': '👹', 'color': arcade.color.RED},
            'TANK': {'count': 0, 'icon': '🛡️', 'color': arcade.color.DARK_RED},
            'SHOOTER': {'count': 0, 'icon': '🏹', 'color': arcade.color.GREEN},
            'FAST': {'count': 0, 'icon': '⚡', 'color': arcade.color.ORANGE},
            'BOSS': {'count': 0, 'icon': '👑', 'color': arcade.color.PURPLE}
        }

        self.inventory = None
        self.inventory_key_pressed = False
        self.spawn_points = []

    def spawn_enemy(self, x, y, enemy_type='BASIC'):
        """Создание врага определенного типа"""
        # Проверяем что позиция не занята
        for enemy in self.enemies:
            if math.sqrt((x - enemy.center_x) ** 2 + (y - enemy.center_y) ** 2) < 60:
                x += random.randint(-30, 30)
                y += random.randint(-30, 30)

        # Создаем врага
        enemy = Enemy(x, y, self.player, enemy_type)

        # Для стреляющих врагов добавляем ссылку на игру
        if enemy_type in ['SHOOTER', 'BOSS']:
            enemy.shoot = lambda: self.enemy_shoot(enemy)

        # Проверяем что враг не в стене
        if self.level:
            if arcade.check_for_collision_with_list(enemy, self.level.collision_sprites):
                print(f"⚠️ {enemy_type} спавнится в стене! Пропускаем...")
                return None

        self.enemies.append(enemy)
        self.enemy_info[enemy_type]['count'] += 1

        # Добавляем свет
        if enemy.light:
            self.light_layer.add(enemy.light)
            self.enemy_lights.append(enemy.light)

        return enemy

    def enemy_shoot(self, enemy):
        """Стрельба врага (стрелка или босса)"""
        if enemy.enemy_type in ['SHOOTER', 'BOSS']:
            dx = self.player.center_x - enemy.center_x
            dy = self.player.center_y - enemy.center_y
            dist = max(1, math.sqrt(dx * dx + dy * dy))

            # Направление стрельбы
            direction = (dx / dist, dy / dist)

            # Настройки пули в зависимости от типа
            if enemy.enemy_type == 'SHOOTER':
                bullet = EnemyBullet(enemy.center_x, enemy.center_y, direction,
                                     damage=SHOOTER_DAMAGE, speed=300)
            else:  # BOSS
                bullet = EnemyBullet(enemy.center_x, enemy.center_y, direction,
                                     damage=15, speed=350)

            self.enemy_bullets.append(bullet)
            self.enemy_bullet_sprites.append(bullet.sprite)
            self.light_layer.add(bullet.light)

            print(f"🔫 {enemy.enemy_type} стреляет!")

    def update_enemy_physics(self, delta_time):
        """Обрабатывает физику врагов"""
        for i, enemy1 in enumerate(self.enemies):
            for enemy2 in self.enemies[i + 1:]:
                dx = enemy1.center_x - enemy2.center_x
                dy = enemy1.center_y - enemy2.center_y
                distance = max(1, math.sqrt(dx * dx + dy * dy))
                min_distance = enemy1.radius + enemy2.radius

                if distance < min_distance:
                    force = (min_distance - distance) / min_distance
                    dx_norm = dx / distance
                    dy_norm = dy / distance
                    push = force * enemy1.push_force * delta_time
                    enemy1.center_x += dx_norm * push
                    enemy1.center_y += dy_norm * push
                    enemy2.center_x -= dx_norm * push
                    enemy2.center_y -= dy_norm * push

    def setup(self):
        """Инициализация игры"""
        try:
            self.level = Level("maps/first_lvl.tmx")

            player_start_x = SCREEN_WIDTH // 2
            player_start_y = SCREEN_HEIGHT // 2

            map_properties = self.level.tile_map.tiled_map.properties
            if map_properties:
                start_x = map_properties.get("player_start_x")
                start_y = map_properties.get("player_start_y")
                if start_x is not None and start_y is not None:
                    player_start_x = float(start_x)
                    player_start_y = float(start_y)

            self.player.center_x = player_start_x
            self.player.center_y = player_start_y

            if hasattr(self.level.tile_map, 'width') and hasattr(self.level.tile_map, 'height'):
                map_width = self.level.tile_map.width * self.level.tile_map.tile_width
                map_height = self.level.tile_map.height * self.level.tile_map.tile_height

                self.camera_left_bound = SCREEN_WIDTH // 2
                self.camera_right_bound = map_width - SCREEN_WIDTH // 2
                self.camera_bottom_bound = SCREEN_HEIGHT // 2
                self.camera_top_bound = map_height - SCREEN_HEIGHT // 2

                if map_width < SCREEN_WIDTH:
                    self.camera_left_bound = map_width // 2
                    self.camera_right_bound = map_width // 2
                if map_height < SCREEN_HEIGHT:
                    self.camera_bottom_bound = map_height // 2
                    self.camera_top_bound = map_height // 2

            self.physics_engine = arcade.PhysicsEngineSimple(
                self.player, self.level.collision_list
            )

            self.player.trail = make_trail(self.player, maintain=60)
            self.emitters.append(self.player.trail)

            self.player.light = Light(
                self.player.center_x,
                self.player.center_y,
                150,
                arcade.color.WHITE,
                'soft'
            )
            self.light_layer.add(self.player.light)

            print("Игра успешно инициализирована")

            self.countdown_time = COUNTDOWN_TIME
            self.countdown_active = True
            self.countdown_text = "5"
            self.game_started = False

            self.inventory = Inventory(self.player)

        except Exception as e:
            print(f"Ошибка в setup(): {e}")
            raise

        self.create_spawn_points()

    def create_spawn_points(self):
        """Создает безопасные точки для спавна врагов"""
        self.spawn_points = []
        for _ in range(20):
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            safe = True

            if self.level:
                temp = arcade.SpriteSolidColor(50, 50, arcade.color.TRANSPARENT_BLACK)
                temp.center_x = x
                temp.center_y = y
                if arcade.check_for_collision_with_list(temp, self.level.collision_sprites):
                    safe = False

            if math.sqrt((x - self.player.center_x) ** 2 + (y - self.player.center_y) ** 2) < 200:
                safe = False

            if safe:
                self.spawn_points.append((x, y))

        print(f"✅ Создано {len(self.spawn_points)} точек для спавна врагов")

    def spawn_wave(self):
        """Спавнит волну врагов разных типов"""
        if len(self.enemies) >= self.max_enemies:
            print("⚠️ Достигнут максимум врагов!")
            return

        # 🔥 РАСЧЕТ ВОЛНЫ
        enemies_to_spawn = self.base_enemies_per_wave + (self.wave_number - 1) * self.enemies_per_wave_increase
        enemies_to_spawn = min(enemies_to_spawn, self.max_enemies - len(self.enemies))

        # Сбрасываем счетчики врагов
        for enemy_type in self.enemy_info:
            self.enemy_info[enemy_type]['count'] = 0

        self.current_wave_enemies = enemies_to_spawn
        self.wave_cleared = False

        # 🔥 СПАВН БОССА КАЖДУЮ 5-Ю ВОЛНУ
        if self.wave_number % BOSS_SPAWN_WAVE == 0 and self.wave_number > 1:
            print(f"👑 БОСС ВОЛНА #{self.wave_number // BOSS_SPAWN_WAVE}")
            # Спавним одного босса вместо обычных врагов
            if self.spawn_points:
                x, y = random.choice(self.spawn_points)
                self.spawn_enemy(x, y, 'BOSS')
                enemies_to_spawn -= 1
                print("🔥 Появился БОСС!")

        # 🔥 РАСПРЕДЕЛЕНИЕ ТИПОВ ВРАГОВ
        for i in range(enemies_to_spawn):
            if self.spawn_points:
                x, y = random.choice(self.spawn_points)

                # Выбираем тип врага в зависимости от номера волны
                if self.wave_number < 3:
                    # Первые 2 волны - только обычные
                    enemy_type = 'BASIC'
                elif self.wave_number < 5:
                    # Волны 3-4 - добавляем быстрых
                    enemy_type = random.choice(['BASIC', 'FAST'])
                elif self.wave_number < 8:
                    # Волны 5-7 - добавляем стрелков
                    enemy_type = random.choice(['BASIC', 'FAST', 'SHOOTER'])
                else:
                    # Волны 8+ - все типы кроме босса
                    enemy_type = random.choice(['BASIC', 'FAST', 'SHOOTER', 'TANK'])

                self.spawn_enemy(x, y, enemy_type)
            else:
                # Если точек нет - спавним по краям
                side = random.choice(['top', 'bottom', 'left', 'right'])
                if side == 'top':
                    x = random.randint(0, SCREEN_WIDTH)
                    y = SCREEN_HEIGHT + 50
                elif side == 'bottom':
                    x = random.randint(0, SCREEN_WIDTH)
                    y = -50
                elif side == 'left':
                    x = -50
                    y = random.randint(0, SCREEN_HEIGHT)
                else:
                    x = SCREEN_WIDTH + 50
                    y = random.randint(0, SCREEN_HEIGHT)

                enemy_type = random.choice(ENEMY_TYPES) if self.wave_number > 2 else 'BASIC'
                self.spawn_enemy(x, y, enemy_type)

        print(f"🌊 Волна {self.wave_number}: {enemies_to_spawn} врагов")
        print(f"   Типы: Базовые={self.enemy_info['BASIC']['count']}, "
              f"Танки={self.enemy_info['TANK']['count']}, "
              f"Стрелки={self.enemy_info['SHOOTER']['count']}, "
              f"Быстрые={self.enemy_info['FAST']['count']}, "
              f"Босс={self.enemy_info['BOSS']['count']}")
        self.wave_number += 1

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)
        if key == arcade.key.TAB or key == arcade.key.I:
            if not self.inventory_key_pressed:
                self.inventory.toggle()
                self.inventory_key_pressed = True

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
        if key == arcade.key.TAB or key == arcade.key.I:
            self.inventory_key_pressed = False

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT and self.can_shoot and not self.countdown_active:
            self.shoot()
            self.can_shoot = False
            arcade.schedule(self.weapon_ready, self.shoot_cooldown)

        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.inventory and self.inventory.check_click(x, y):
                return

    def weapon_ready(self, delta_time):
        self.can_shoot = True
        arcade.unschedule(self.weapon_ready)

    def shoot(self):
        """Создание пули игрока"""
        bullet = Bullet(self.player.center_x, self.player.center_y, self.player.shoot_direction)
        self.bullets.append(bullet)
        self.bullet_sprites.append(bullet.sprite)
        self.emitters.append(bullet.trail)
        self.light_layer.add(bullet.light)

    def update_camera(self):
        self.game_camera.center(self.player.center_x, self.player.center_y)

    def update_player_movement(self, delta_time):
        dx, dy = 0, 0
        if arcade.key.LEFT in self.keys_pressed or arcade.key.A in self.keys_pressed:
            dx -= self.player.speed * delta_time
        if arcade.key.RIGHT in self.keys_pressed or arcade.key.D in self.keys_pressed:
            dx += self.player.speed * delta_time
        if arcade.key.UP in self.keys_pressed or arcade.key.W in self.keys_pressed:
            dy += self.player.speed * delta_time
        if arcade.key.DOWN in self.keys_pressed or arcade.key.S in self.keys_pressed:
            dy -= self.player.speed * delta_time

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        if dx != 0 or dy != 0:
            self.player.update_direction(dx, dy)

        self.player.change_x = dx
        self.player.change_y = dy

        if self.physics_engine:
            self.physics_engine.update()

        if self.player.trail:
            self.player.trail.center_x = self.player.center_x
            self.player.trail.center_y = self.player.center_y
        if self.player.light:
            self.player.light.position = (self.player.center_x, self.player.center_y)

    def on_update(self, delta_time):
        # 🔥 ОТСЧЕТ
        if self.countdown_active:
            self.countdown_time -= delta_time

            if self.countdown_time > 0:
                seconds = int(self.countdown_time) + 1
                self.countdown_text = f"{seconds}"
                if seconds <= 3:
                    self.countdown_text = f"🎮 {seconds}!"
            else:
                self.countdown_active = False
                self.countdown_text = "СТАРТ!"
                self.game_started = True
                print("🚀 Игра началась!")
                self.spawn_wave()

            self.update_player_movement(delta_time)
            self.update_camera()

            for emitter in self.emitters:
                emitter.update()
            return

        if not self.game_started:
            return

        # 🔥 ОБНОВЛЕНИЕ ИГРОКА
        self.update_player_movement(delta_time)

        # 🔥 ВОЛНЫ
        if not self.wave_cleared and len(self.enemies) == 0:
            self.wave_cleared = True
            print(f"✅ Волна зачищена! Следующая волна через {self.spawn_interval} секунд")
            self.spawn_timer = 0

        if self.wave_cleared:
            self.spawn_timer += delta_time
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_wave()
                self.spawn_timer = 0

        # 🔥 ОБНОВЛЕНИЕ ВРАГОВ
        self.enemies.update(delta_time)
        self.update_enemy_physics(delta_time)

        # 🔥 ОБНОВЛЕНИЕ ВРАЖЕСКИХ ПУЛЬ
        enemy_bullets_to_remove = []
        for bullet in self.enemy_bullets[:]:
            should_remove = bullet.update(delta_time)

            # Проверка попадания в игрока
            distance = math.sqrt(
                (bullet.sprite.center_x - self.player.center_x) ** 2 +
                (bullet.sprite.center_y - self.player.center_y) ** 2
            )
            if distance < bullet.radius + self.player.width / 2:
                self.player.health -= bullet.damage
                print(f"💥 Игрок получил {bullet.damage} урона от вражеской пули! Здоровье: {self.player.health}")
                should_remove = True

            if should_remove:
                enemy_bullets_to_remove.append(bullet)

        for bullet in enemy_bullets_to_remove:
            if bullet.light in self.light_layer._lights:
                self.light_layer.remove(bullet.light)
            if bullet.sprite in self.enemy_bullet_sprites:
                self.enemy_bullet_sprites.remove(bullet.sprite)
            if bullet in self.enemy_bullets:
                self.enemy_bullets.remove(bullet)

        # 🔥 ПРОВЕРКА ГРАНИЦ И СТЕН
        for enemy in self.enemies[:]:
            if enemy.center_x < 50:
                enemy.center_x = 50
            elif enemy.center_x > SCREEN_WIDTH - 50:
                enemy.center_x = SCREEN_WIDTH - 50

            if enemy.center_y < 50:
                enemy.center_y = 50
            elif enemy.center_y > SCREEN_HEIGHT - 50:
                enemy.center_y = SCREEN_HEIGHT - 50

            if self.level:
                wall_collisions = arcade.check_for_collision_with_list(enemy, self.level.collision_sprites)
                if wall_collisions:
                    for wall in wall_collisions:
                        dx = enemy.center_x - wall.center_x
                        dy = enemy.center_y - wall.center_y
                        dist = max(1, math.sqrt(dx * dx + dy * dy))
                        enemy.center_x += (dx / dist) * 5
                        enemy.center_y += (dy / dist) * 5

        # 🔥 ПУЛИ ИГРОКА
        bullets_to_remove = []
        for bullet in self.bullets[:]:
            should_remove = bullet.update(delta_time)

            # Столкновение со стенами
            bullet_hit_wall = False
            if self.level:
                for wall in self.level.collision_sprites:
                    distance = math.sqrt(
                        (bullet.sprite.center_x - wall.center_x) ** 2 +
                        (bullet.sprite.center_y - wall.center_y) ** 2
                    )
                    if distance < bullet.radius + wall.width / 2:
                        bullet_hit_wall = True
                        break

            # Столкновение с врагами
            bullet_hit_enemy = False
            for enemy in self.enemies[:]:
                distance = math.sqrt(
                    (bullet.sprite.center_x - enemy.center_x) ** 2 +
                    (bullet.sprite.center_y - enemy.center_y) ** 2
                )
                enemy_radius = enemy.width / 2 if hasattr(enemy, 'width') else 15
                if distance < bullet.radius + enemy_radius:
                    bullet_hit_enemy = True
                    damage_dealt = enemy.take_damage(10)  # Базовый урон 10

                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.enemy_info[enemy.enemy_type]['count'] -= 1
                        if enemy.light in self.light_layer._lights:
                            self.light_layer.remove(enemy.light)
                        enemy.die(self)
                        print(f"💀 {enemy.enemy_type} уничтожен!")
                    break

            if should_remove or bullet_hit_wall or bullet_hit_enemy:
                bullets_to_remove.append(bullet)

        for bullet in bullets_to_remove:
            if bullet.trail in self.emitters:
                self.emitters.remove(bullet.trail)
            if bullet.light in self.light_layer._lights:
                self.light_layer.remove(bullet.light)
            if bullet.sprite in self.bullet_sprites:
                self.bullet_sprites.remove(bullet.sprite)
            if bullet in self.bullets:
                self.bullets.remove(bullet)

        # 🔥 ЭМИТТЕРЫ
        for emitter in self.emitters:
            emitter.update()

        # 🔥 ПРОВЕРКА СМЕРТИ ИГРОКА
        if self.player.health <= 0 and self.game_started:
            print("💀 ИГРА ОКОНЧЕНА!")
            self.game_started = False
            # Здесь можно добавить экран Game Over

        self.update_camera()

    def on_draw(self):
        self.clear()
        self.game_camera.use()

        if self.level and hasattr(self.level, 'background'):
            self.level.background.draw()

        with self.light_layer:
            if self.level and hasattr(self.level, 'walls'):
                self.level.walls.draw()
            self.enemies.draw()
            self.player_list.draw()
            self.bullet_sprites.draw()
            self.enemy_bullet_sprites.draw()  # 🔥 Рисуем вражеские пули

        self.light_layer.draw(ambient_color=(20, 20, 20))

        for emitter in self.emitters:
            emitter.draw()

        self.gui_camera.use()
        self.draw_hud()

        if self.countdown_active:
            self.draw_countdown()

        if self.inventory:
            self.inventory.draw()

    def draw_countdown(self):
        arcade.draw_lrbt_rectangle_filled(
            left=0,  # Начинаем от самого левого края экрана
            right=SCREEN_WIDTH,  # До самого правого края
            bottom=0,  # От самого нижнего края
            top=SCREEN_HEIGHT,  # До самого верхнего края
            color=(0, 0, 0, 150)
        )

        if self.countdown_time > 3:
            color = arcade.color.WHITE
            font_size = 120
        elif self.countdown_time > 0:
            color = arcade.color.YELLOW
            font_size = 140
        else:
            color = arcade.color.GREEN
            font_size = 100

        arcade.draw_text(
            self.countdown_text,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            color,
            font_size,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        arcade.draw_text(
            "Можно двигаться во время отсчета!",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 100,
            arcade.color.LIGHT_GRAY,
            24,
            anchor_x="center",
            anchor_y="center"
        )

        arcade.draw_text(
            "Управление: WASD/Стрелки - движение, ЛКМ - стрельба",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 150,
            arcade.color.LIGHT_GRAY,
            20,
            anchor_x="center",
            anchor_y="center"
        )

        arcade.draw_text(
            "Tab/I - инвентарь прокачки",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 180,
            arcade.color.LIGHT_GRAY,
            20,
            anchor_x="center",
            anchor_y="center"
        )

    def draw_hud(self):
        # Здоровье игрока
        arcade.draw_text(
            f"HP: {self.player.health}/{self.player.max_health}",
            20, SCREEN_HEIGHT - 35,
            arcade.color.WHITE, 20
        )

        # Полоска здоровья
        bar_left = 20
        bar_right = 220
        bar_top = SCREEN_HEIGHT - 60
        bar_bottom = SCREEN_HEIGHT - 75

        arcade.draw_lrbt_rectangle_filled(
            left=bar_left,
            right=bar_right,
            bottom=bar_bottom,  # Внимание: порядок аргументов!
            top=bar_top,
            color=arcade.color.DARK_GRAY
        )

        health_percent = max(0, self.player.health / self.player.max_health)
        health_right = bar_left + (bar_right - bar_left) * health_percent

        if health_percent > 0.7:
            health_color = arcade.color.WHITE
        elif health_percent > 0.3:
            health_color = arcade.color.WHITE_SMOKE
        else:
            health_color = arcade.color.LIGHT_GRAY

        if health_percent > 0:
            arcade.draw_lrbt_rectangle_filled(
                left=bar_left,
                right=health_right,
                bottom=bar_bottom,
                top=bar_top,
                color=health_color
            )

        arcade.draw_lrbt_rectangle_outline(
            left=bar_left,
            right=bar_right,
            bottom=bar_bottom,
            top=bar_top,
            color=arcade.color.GRAY,
            border_width=2
        )

        # 🔥 ИНФОРМАЦИЯ О ТИПАХ ВРАГОВ (правый верх)
        y_offset = SCREEN_HEIGHT - 35
        for enemy_type, info in self.enemy_info.items():
            if info['count'] > 0:
                icon = info['icon']
                color = info['color']
                arcade.draw_text(
                    f"{icon} {enemy_type}: {info['count']}",
                    SCREEN_WIDTH - 200, y_offset,
                    color, 14
                )
                y_offset -= 25

        # Волна
        wave_info = f"Волна: {self.wave_number - 1}"
        if not self.wave_cleared and self.current_wave_enemies > 0:
            enemies_left = len(self.enemies)
            wave_info += f" ({enemies_left}/{self.current_wave_enemies})"

        arcade.draw_text(
            wave_info,
            SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 35,
            arcade.color.CYAN, 16
        )

        # Таймер следующей волны
        if self.wave_cleared and self.spawn_interval - self.spawn_timer > 0:
            time_left = self.spawn_interval - self.spawn_timer
            arcade.draw_text(
                f"След. волна: {time_left:.1f}с",
                SCREEN_WIDTH - 150, SCREEN_HEIGHT - 85,
                arcade.color.YELLOW, 14
            )
        elif not self.wave_cleared:
            arcade.draw_text(
                "Убейте всех врагов!",
                SCREEN_WIDTH - 160, SCREEN_HEIGHT - 105,
                arcade.color.RED, 14
            )

        # Очки навыков
        if self.player.skill_points > 0:
            arcade.draw_text(
                f"🎯 {self.player.skill_points} оч. навыков (Tab)",
                SCREEN_WIDTH - 200, SCREEN_HEIGHT - 160,
                arcade.color.GOLD, 14,
                bold=True
            )

        # Опыт
        xp_percent = min(1.0, self.player.xp / self.player.xp_to_next_level)
        xp_left = 20
        xp_right = xp_left + 200
        xp_top = SCREEN_HEIGHT - 140
        xp_bottom = SCREEN_HEIGHT - 150

        if xp_bottom >= xp_top:
            xp_bottom, xp_top = xp_top, xp_bottom

        arcade.draw_lrbt_rectangle_filled(
            left=xp_left,
            right=xp_right,
            bottom=xp_bottom,
            top=xp_top,
            color=arcade.color.DARK_GREEN
        )

        if xp_percent > 0:
            current_xp_width = 200 * xp_percent
            arcade.draw_lrbt_rectangle_filled(
                left=xp_left,
                right=xp_left + current_xp_width,
                bottom=xp_bottom,
                top=xp_top,
                color=arcade.color.LIME
            )

        arcade.draw_text(
            f"Ур. {self.player.level} | {self.player.xp}/{self.player.xp_to_next_level} XP",
            20, SCREEN_HEIGHT - 170,
            arcade.color.GREEN, 14
        )


def main():
    try:
        import arcade
        print(f"Версия Arcade: {arcade.__version__}")
        print("🎮 Игра с 4 типами врагов и боссом!")
        print("Типы врагов:")
        print("👹 Базовый - обычный враг")
        print("🛡️ Танк - много здоровья, медленный, сильный удар")
        print("🏹 Стрелок - стреляет издалека")
        print("⚡ Быстрый - очень быстрый, но слабый")
        print("👑 Босс - появляется каждую 5-ю волну, очень сильный")

        # Создаем папку для текстур врагов, если её нет
        if not os.path.exists("textures/enemies"):
            os.makedirs("textures/enemies")
            print("📁 Создана папка для текстур врагов: textures/enemies/")
            print("📝 Форматы имен файлов, которые поддерживаются:")
            print("   1. basic_up_0.png, basic_up_1.png (рекомендуемый)")
            print("   2. bas_up_0.png, bas_up_1.png (сокращенный)")
            print("   3. enemy_basic_up_0.png (с приставкой enemy_)")

        game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
        game.setup()
        arcade.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()