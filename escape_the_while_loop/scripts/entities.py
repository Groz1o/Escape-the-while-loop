import pygame as pg
from pygame.locals import *
import random
import math

from scripts.wave import Wave
from scripts.spark import Spark
from scripts.particle import Particle, ParticleSystem

class Player:
    def __init__(self, game, tilemap, pos):
        self.game = game
        self.tilemap = tilemap
        self.status = "run"
        #images
        self.images = self.game.assets["player/" + self.status]
        self.image = self.images.render_image()
        self.rect = self.image.get_rect(topleft = pos)
        self.flip = False
        self.img_alpha = 255
        #dashing
        self.dash = False
        self.dash_count = 0
        self.dash_timer = 40
        self.dash_velocity = 20
        self.dash_direction = None
        #speed
        self.speed = 5
        self.gravity = 0.7
        self.velocity = [0, 0]
        #jumping
        self.jumps = 1
        self.in_air = False
        self.air_time = 0
        #particle system
        self.particle_system = ParticleSystem()

    def set_status(self, status):
        if self.status != status:
            self.status = status
            self.images = self.game.assets["player/" + self.status]
            if "player" in status:
                for asset_key in list(self.game.assets.keys())[:2]:
                    if asset_key != "player/" + self.status:
                        self.game.assets[asset_key].frame_index = 0

    def jump(self):
        if self.jumps:
            self.jumps = max(0, self.jumps - 1)
            self.velocity[1] = -14

    def update(self, movement):
        if not self.game.dead:
            frame_movement = [movement * self.speed + self.velocity[0], self.velocity[1]]

            self.velocity[1] = min(self.velocity[1] + self.gravity, 15)

            #check_flip
            keys = pg.key.get_pressed()
            if keys[K_LEFT]:
                self.flip = True
            elif keys[K_RIGHT]:
                self.flip = False

            #dashing
            if self.dash:
                self.particle_system.emit(self.rect.centerx, self.rect.centery)
                if not self.dash_direction:
                    self.dash_direction = "left" if self.flip else "right"
                self.dash_count += 1
                frame_movement[0] += self.dash_velocity if self.dash_direction == "right" else -self.dash_velocity
                if self.dash_count >= 8:
                    self.dash = False
                    self.dash_timer = 0
            else:
                self.dash_count = 0
                self.dash_timer += 1
                self.dash_direction = None

            #collisions
            collisions = {"up": False, "down": False, "left": False, "right": False}

            self.rect.x += frame_movement[0]
            for tile_pos in self.tilemap.collidable_tiles.values():
                tile_rect = pg.Rect(tile_pos[0] * self.game.tile_size, tile_pos[1] * self.game.tile_size, self.game.tile_size, self.game.tile_size - 16)
                if self.rect.colliderect(tile_rect):
                    if frame_movement[0] > 0:
                        collisions["right"] = True
                        self.rect.right = tile_rect.left
                    elif frame_movement[0] < 0:
                        collisions["left"] = True
                        self.rect.left = tile_rect.right

            self.rect.y += frame_movement[1]
            for tile_pos in self.tilemap.collidable_tiles.values():
                tile_rect = pg.Rect(tile_pos[0] * self.game.tile_size, tile_pos[1] * self.game.tile_size, self.game.tile_size, self.game.tile_size  - 16)
                if self.rect.colliderect(tile_rect):
                    if frame_movement[1] > 0:
                        collisions["down"] = True
                        self.rect.bottom = tile_rect.top
                    elif frame_movement[1] < 0:
                        collisions["up"] = True
                        self.rect.top = tile_rect.bottom

            self.rect.left = max(0, self.rect.left)
            self.rect.right = min(2016, self.rect.right)

            if collisions["up"] or collisions["down"]:
                self.velocity[1] = 0

            #set status
            if frame_movement[0] != 0:
                self.set_status("run")
            else:
                self.set_status("idle")

            if collisions["down"]:
                self.in_air = False
                self.jumps = 1
            else:
                self.in_air = True

            if self.in_air:
                self.air_time += 1
            else:
                self.air_time = 0

            #image update
            self.images.update()
            self.image = self.images.render_image()
            self.img_alpha = 0 if self.dash else 255
        else:
            self.img_alpha = 0

    def render(self, display, offset):
        self.image.set_alpha(self.img_alpha)
        display.blit(pg.transform.flip(self.image, self.flip, False), (self.rect.x - offset[0], self.rect.y - offset[1]))
        self.particle_system.draw(display, offset)

class SquareBracketEnemy:
    def __init__(self, game, tilemap, pos):
        self.game = game
        self.tilemap = tilemap
        self.status = "idle"
        self.frame_index = 0
        self.images = self.game.assets["squre_bracket_enemy/" + self.status]
        self.image = self.images.render_image()
        self.rect = self.image.get_rect(topleft = pos)
        self.flip = False
        #movement
        self.walk = False
        self.speed = 2
        self.velocity = [0, 0]
        self.gravity = 0.7
        #self destruct
        self.self_destruct = False
        #sword vars
        self.sword_run_image = self.game.assets["sword_run"]
        self.sword_attack_image = self.game.assets["sword_attack"]
        self.sword_pos = [self.rect.center[0] - 25, self.rect.center[1] - 50] if not self.flip else [self.rect.center[0] + 10, self.rect.center[1] - 15]
        #attack vars
        self.attack_timer = 0
        self.attack_cooldown = 15
        self.attack_bar_pos = [self.rect.topleft[0] + 10, self.rect.topleft[1] - 25] if not self.flip else [self.rect.topleft[0] - 18, self.rect.topleft[1] - 25]
        #attacking vars
        self.attacking = False
        self.attacking_timer = 0
        self.attacking_cooldown = 10
        #y distance
        self.y_distance = 0

    def set_status(self, status):
        if self.status != status:
            self.status = status
            self.images = self.game.assets["squre_bracket_enemy/" + self.status]

    def render_attack_bar(self, current_ammount, max_ammount, pos, display):
        bar_lenght = 90
        bar_height = 20

        ratio = current_ammount / max_ammount
        filled_bar_lenght = int(bar_lenght * ratio)

        #check for attack
        if filled_bar_lenght == bar_lenght:
            self.attacking = True
            self.attack_timer = 0

        pg.draw.rect(display, "white", pg.Rect(*pos, bar_lenght, bar_height))

        pg.draw.rect(display, "red", pg.Rect(*pos, filled_bar_lenght, bar_height))

    def check_walk(self, player_centerx, player_bottom):
        center = self.rect.centerx
        x_distance = abs(player_centerx - center)
        self.y_distance = abs(player_bottom - self.rect.bottom)

        if self.y_distance >= 0 and self.y_distance <= 150:
            #check walk
            if x_distance <= 400 and x_distance >= 30:
                self.walk = True
            else:
                self.walk = False

            #update status
            if x_distance <= 400:
                self.set_status("run")
            else:
                self.set_status("idle")

            #check attack
            if x_distance <= 30 and not self.attacking:
                self.attack_timer = min(self.attack_cooldown, self.attack_timer + 0.4)
            else:
                self.attack_timer = max(0, self.attack_timer - 0.4)

            if self.attacking:
                self.attacking_timer += 0.3

            if self.attacking_timer >= self.attacking_cooldown:
                self.attacking = False
                self.attacking_timer = 0
            
            if self.attacking and x_distance <= 30:
                self.game.dead = True

            #update attack bar position
            self.attack_bar_pos = [self.rect.topleft[0] - 5, self.rect.topleft[1] - 25] if not self.flip else [self.rect.topleft[0] - 15, self.rect.topleft[1] - 25]

            #check flip
            if player_centerx < self.rect.centerx:
                self.flip = False
            elif player_centerx > self.rect.centerx:
                self.flip = True

    def update(self, player_pos):
        if not self.attacking:
            frame_movement = [self.velocity[0], self.velocity[1]]

            self.velocity[1] = min(self.velocity[1] + self.gravity, 15)

            if self.walk:
                self.velocity[0] = self.speed if self.flip else -self.speed
            else:
                self.velocity[0] = 0

            self.rect.x += frame_movement[0]

            #collisions
            collisions = {"up": False, "down": False, "left": False, "right": False}

            self.rect.y += frame_movement[1]
            for tile_pos in self.tilemap.collidable_tiles.values():
                tile_rect = pg.Rect(tile_pos[0] * self.game.tile_size, tile_pos[1] * self.game.tile_size, self.game.tile_size, self.game.tile_size  - 16)
                if self.rect.colliderect(tile_rect):
                    if frame_movement[1] > 0:
                        collisions["down"] = True
                        self.rect.bottom = tile_rect.top
                    elif frame_movement[1] < 0:
                        collisions["up"] = True
                        self.rect.top = tile_rect.bottom

            #sword position update
            self.sword_pos = [self.rect.center[0] - 25, self.rect.center[1] - 50] if not self.flip else [self.rect.center[0] + 29, self.rect.center[1] - 50]

            #image update
            self.images.update()
            self.image = self.images.render_image()

    def render(self, display, offset):
        display.blit(pg.transform.flip(self.image, self.flip, False), (self.rect.x - offset[0], self.rect.y - offset[1]))

        if self.status == "run":
            if self.attacking:
                rotated_sword_img = pg.transform.rotate(self.sword_run_image, 90)
                new_sword_pos = (self.sword_pos[0] + 5 - offset[0], self.sword_pos[1] + 28 - offset[1]) if self.flip else (self.sword_pos[0] - 30 - offset[0], self.sword_pos[1] + 28 - offset[1])
                
                display.blit(pg.transform.flip(rotated_sword_img, self.flip, False), new_sword_pos)
            else:
                display.blit(pg.transform.flip(self.sword_run_image, self.flip, False), (self.sword_pos[0] - offset[0], self.sword_pos[1] - offset[1]))
            self.render_attack_bar(self.attack_timer, self.attack_cooldown, (self.attack_bar_pos[0] - offset[0], self.attack_bar_pos[1] - offset[1]), display)

class CurlyBracketEnemy:
    def __init__(self, game, tilemap, pos):
        self.game = game
        self.tilemap = tilemap
        self.status = "idle"
        self.frame_index = 0
        self.images = self.game.assets["curly_bracket_enemy/" + self.status]
        self.image = self.images.render_image()
        self.rect = self.image.get_rect(topleft = pos)
        self.flip = False
        #movement
        self.walk = False
        self.speed = 2
        self.velocity = [0, 0]
        self.gravity = 0.7
        #explode vars
        self.explode = False
        self.explode_timer = 0
        self.explode_cooldown = 30
        self.explode_bar_pos = [self.rect.topleft[0] + 10, self.rect.topleft[1] - 25] if not self.flip else [self.rect.topleft[0] - 18, self.rect.topleft[1] - 25]
        #self destruct
        self.self_destruct = False
        #y distance
        self.y_distance = 0

    def set_status(self, status):
        if self.status != status:
            self.status = status
            self.images = self.game.assets["curly_bracket_enemy/" + self.status]

    def render_explode_bar(self, current_ammount, max_ammount, pos, display):
        bar_lenght = 90
        bar_height = 20

        ratio = current_ammount / max_ammount
        filled_bar_lenght = int(bar_lenght * ratio)

        pg.draw.rect(display, "white", pg.Rect(*pos, bar_lenght, bar_height))

        pg.draw.rect(display, "red", pg.Rect(*pos, filled_bar_lenght, bar_height))

    def check_walk(self, player_centerx, player_bottom):
        center = self.rect.centerx
        x_distance = abs(player_centerx - center)
        self.y_distance = abs(player_bottom - self.rect.bottom)

        if self.y_distance >= 0 and self.y_distance <= 150:
            #check walk
            if x_distance <= 400 and x_distance >= 200:
                self.walk = True
            else:
                self.walk = False

            #check explode
            if x_distance <= 200:
                self.explode_timer += 0.3
            else:
                self.explode_timer = max(0, self.explode_timer - 0.3)

            if self.explode_timer >= self.explode_cooldown:
                self.explode = True

            #update explode bar position
            self.explode_bar_pos = [self.rect.topleft[0] + 10, self.rect.topleft[1] - 25] if not self.flip else [self.rect.topleft[0] - 18, self.rect.topleft[1] - 25]

            #update status
            if x_distance <= 400:
                self.set_status("run")
            else:
                self.set_status("idle")

            #check flip
            if player_centerx < self.rect.centerx:
                self.flip = False
            elif player_centerx > self.rect.centerx:
                self.flip = True

    def update(self, player_pos):
        frame_movement = [self.velocity[0], self.velocity[1]]

        self.velocity[1] = min(self.velocity[1] + self.gravity, 15)

        if self.walk:
            self.velocity[0] = self.speed if self.flip else -self.speed
        else:
            self.velocity[0] = 0

        self.rect.x += frame_movement[0]

        #collisions
        collisions = {"up": False, "down": False, "left": False, "right": False}

        self.rect.y += frame_movement[1]
        for tile_pos in self.tilemap.collidable_tiles.values():
            tile_rect = pg.Rect(tile_pos[0] * self.game.tile_size, tile_pos[1] * self.game.tile_size, self.game.tile_size, self.game.tile_size  - 16)
            if self.rect.colliderect(tile_rect):
                if frame_movement[1] > 0:
                    collisions["down"] = True
                    self.rect.bottom = tile_rect.top
                elif frame_movement[1] < 0:
                    collisions["up"] = True
                    self.rect.top = tile_rect.bottom

        if self.explode:
            self.explode = False
            self.self_destruct = True
            self.game.waves.append(Wave(self.rect.center))

        #image update
        self.images.update()
        self.image = self.images.render_image()

    def render(self, display, offset):
        display.blit(pg.transform.flip(self.image, self.flip, False), (self.rect.x - offset[0], self.rect.y - offset[1]))

        if self.status == "run":
            self.render_explode_bar(self.explode_timer, self.explode_cooldown, (self.explode_bar_pos[0] - offset[0], self.explode_bar_pos[1] - offset[1]), display)

class NormalBracketEnemy:
    def __init__(self, game, tilemap, pos):
        self.game = game
        self.tilemap = tilemap
        self.status = "idle"
        self.frame_index = 0
        self.images = self.game.assets["normal_bracket_enemy/" + self.status]
        self.image = self.images.render_image()
        self.rect = self.image.get_rect(topleft = pos)
        self.flip = False
        #movement
        self.walk = False
        self.speed = 2
        self.velocity = [0, 0]
        self.gravity = 0.7
        #gun
        self.gun_image = self.game.assets["gun"]
        self.gun_pos = [self.rect.center[0] - 47, self.rect.center[1] - 25] if not self.flip else [self.rect.center[0] + 20, self.rect.center[1] - 25]
        self.gun_angle = None
        #shoot vars
        self.shoot_timer = 0
        self.shoot_cooldown = 1500
        self.projectiles = []
        self.projectile_speed = 5
        self.projectile_size = 6
        #self destruct
        self.self_destruct = False
        #y distance
        self.y_distance = 0

    def set_status(self, status):
        if self.status != status:
            self.status = status
            self.images = self.game.assets["normal_bracket_enemy/" + self.status]

    def check_walk(self, player_centerx, player_bottom):
        center = self.rect.centerx
        x_distance = abs(player_centerx - center)
        self.y_distance = abs(player_bottom - self.rect.bottom)

        if self.y_distance >= 0 and self.y_distance <= 150:
            if x_distance <= 400 and x_distance >= 200:
                self.walk = True
            else:
                self.walk = False

            if x_distance <= 400:
                self.set_status("run")
            else:
                self.set_status("idle")

            if player_centerx < self.rect.centerx:
                self.flip = False
            elif player_centerx > self.rect.centerx:
                self.flip = True

    def calculate_gun_angle(self, player_x, player_y):
        delta_x = player_x - self.gun_pos[0]
        delta_y = player_y - self.gun_pos[1]

        if self.flip:
            angle = math.degrees(math.atan2(delta_y, delta_x))
        else:
            angle = math.degrees(math.atan2(delta_y, -delta_x))

        return angle

    def calculate_direction(self, player_x, player_y):
        delta_x = player_x - self.gun_pos[0]
        delta_y = player_y - self.gun_pos[1]
        distance = math.sqrt(delta_x ** 2 + delta_y ** 2)
        if distance == 0:
            return (0, 0)
        return (delta_x / distance, delta_y / distance)

    def fire_projectile(self, direction):
        projectile = {
            "pos": [self.gun_pos[0]  + self.projectile_size, self.gun_pos[1]  + self.projectile_size],
            "dir": direction
        }

        self.projectiles.append(projectile)
        self.game.projectiles.append(projectile)

    def move_projectiles(self):
        for projectile in self.projectiles:
            projectile["pos"][0] += projectile["dir"][0] * self.projectile_speed
            projectile["pos"][1] += projectile["dir"][1] * self.projectile_speed

        #TODO remove projectile after a certain time

    def update(self, player_pos):
        frame_movement = [self.velocity[0], self.velocity[1]]

        self.gun_angle = self.calculate_gun_angle(player_pos[0], player_pos[1])

        self.velocity[1] = min(self.velocity[1] + self.gravity, 15)

        if self.walk:
            self.velocity[0] = self.speed if self.flip else -self.speed
        else:
            self.velocity[0] = 0

        self.rect.x += frame_movement[0]

        #collisions
        collisions = {"up": False, "down": False, "left": False, "right": False}

        self.rect.y += frame_movement[1]
        for tile_pos in self.tilemap.collidable_tiles.values():
            tile_rect = pg.Rect(tile_pos[0] * self.game.tile_size, tile_pos[1] * self.game.tile_size, self.game.tile_size, self.game.tile_size  - 16)
            if self.rect.colliderect(tile_rect):
                if frame_movement[1] > 0:
                    collisions["down"] = True
                    self.rect.bottom = tile_rect.top
                elif frame_movement[1] < 0:
                    collisions["up"] = True
                    self.rect.top = tile_rect.bottom

        #update gun pos
        self.gun_pos = [self.rect.center[0] - 47, self.rect.center[1] - 25] if not self.flip else [self.rect.center[0] + 20, self.rect.center[1] - 25]

        #shoot
        cur_time = pg.time.get_ticks()
        
        if cur_time - self.shoot_timer >= self.shoot_cooldown and self.status == "run":
            self.shoot_timer = cur_time
            
            direction = self.calculate_direction(player_pos[0], player_pos[1])
            self.fire_projectile(direction)

        self.move_projectiles()

        #image update
        self.images.update()
        self.image = self.images.render_image()

    def render(self, display, offset):
        rotated_gun_image = pg.transform.rotate(self.gun_image, self.gun_angle)
        display.blit(pg.transform.flip(self.image, self.flip, False), (self.rect.x - offset[0], self.rect.y - offset[1]))
        if self.status == "run":
            display.blit(pg.transform.flip(rotated_gun_image, self.flip, False), (self.gun_pos[0] - offset[0], self.gun_pos[1] - offset[1]))

        for projectile in self.projectiles:
            pg.draw.rect(display, "gray", pg.Rect(projectile["pos"][0] - offset[0], projectile["pos"][1] - offset[1], self.projectile_size, self.projectile_size))
