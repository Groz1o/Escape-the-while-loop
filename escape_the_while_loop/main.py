import pygame as pg
from pygame.locals import *
import sys
import math
import random

from scripts.utils import load_image, load_images, Animation
from scripts.entities import Player, SquareBracketEnemy, CurlyBracketEnemy, NormalBracketEnemy
from scripts.tilemap import Tilemap
from scripts.spark import Spark

class Game:
    def __init__(self):
        self.window_size = (700, 700)
        self.display = pg.display.set_mode(self.window_size)
        self.clock = pg.time.Clock()

        self.tile_size = 32

        self.assets = {
            "player/idle": Animation(load_images("player/idle", 4), 180),
            "player/run": Animation(load_images("player/run", 4), 130),
            "squre_bracket_enemy/idle": Animation(load_images("square_bracket_enemy/idle", 2.5), 300),
            "squre_bracket_enemy/run": Animation(load_images("square_bracket_enemy/run", 2.5)),
            "curly_bracket_enemy/idle": Animation(load_images("curly_bracket_enemy/idle", 2.5), 300),
            "curly_bracket_enemy/run": Animation(load_images("curly_bracket_enemy/run", 2.5)),
            "normal_bracket_enemy/idle": Animation(load_images("normal_bracket_enemy/idle", 2.5), 300),
            "normal_bracket_enemy/run": Animation(load_images("normal_bracket_enemy/run", 2.5)),
            "gun": load_image("normal_bracket_enemy/gun.png", 3),
            "sword_run": load_image("square_bracket_enemy/sword_run.png", 2.5),
            "sword_attack": load_image("square_bracket_enemy/sword_attack.png", 2.5),
            "while": load_image("while.png", 7),
            "true": load_image("true.png", 7),
            "tile": load_image("tile.png", None, (self.tile_size, self.tile_size//2)),
            "one": load_image("numbers/1.png", 10),
            "two": load_image("numbers/2.png", 10),
            "three": load_image("numbers/3.png", 10),
            "four": load_image("numbers/4.png", 10),
            "five": load_image("numbers/5.png", 10),
        }

        self.movement = [False, False]
        self.scroll = [0, 0]

        self.tilemap = Tilemap(self, self.tile_size)
        self.tilemap.load_map()

        #player vars
        self.dead = False
        self.dead_counter = 0

        self.beat_game = False

        self.enemies = []

        self.sparks = []

        self.projectiles = []
        self.projectile_size = 6

        self.waves = []

        self.while_img = self.assets["while"]
        self.true_img = self.assets["true"]
        self.one = self.assets["one"]
        self.two = self.assets["two"]
        self.three = self.assets["three"]
        self.four = self.assets["four"]
        self.five = self.assets["five"]

        self.load_level()

    def blit_ide_stuff(self, render_scroll):
        self.display.blit(self.while_img, (10 - render_scroll[0], -150 - render_scroll[1]))
        self.display.blit(self.true_img, (500 - render_scroll[0], -145 - render_scroll[1]))
        self.display.blit(self.one, (10 - render_scroll[0], 25 - render_scroll[1]))
        self.display.blit(self.two, (10 - render_scroll[0], 325 - render_scroll[1]))
        self.display.blit(self.three, (10 - render_scroll[0], 570 - render_scroll[1]))
        self.display.blit(self.four, (5 - render_scroll[0], 840 - render_scroll[1]))
        self.display.blit(self.five, (10 - render_scroll[0], 1085 - render_scroll[1]))

    def load_level(self):
        self.enemies = []
        self.projectiles = []
        self.waves = []

        for entitiy in self.tilemap.spawners.values():
            if entitiy[0] == "player":
                self.player = Player(self, self.tilemap, (entitiy[1][0] * self.tile_size, entitiy[1][1] * self.tile_size))
            elif entitiy[0] == "squre_bracket_enemy":
                self.enemies.append(SquareBracketEnemy(self, self.tilemap, (entitiy[1][0] * self.tile_size, entitiy[1][1] * self.tile_size)))
            elif entitiy[0] == "curly_bracket_enemy":
                self.enemies.append(CurlyBracketEnemy(self, self.tilemap, (entitiy[1][0] * self.tile_size, entitiy[1][1] * self.tile_size)))
            elif entitiy[0] == "normal_bracket_enemy":
                self.enemies.append(NormalBracketEnemy(self, self.tilemap, (entitiy[1][0] * self.tile_size, entitiy[1][1] * self.tile_size)))

    def run(self):
        pg.init()
        pg.display.set_caption("Escape the while loop")

        while True:
            for e in pg.event.get():
                if e.type == QUIT:
                    pg.quit()
                    sys.exit()
                if e.type == KEYDOWN:
                    if e.key == K_RIGHT:
                        self.movement[1] = True
                    if e.key == K_LEFT:
                        self.movement[0] = True
                    if e.key == K_SPACE or e.key == K_UP:
                        self.player.jump()
                    if e.key == K_x and self.player.dash_timer >= 40:
                        self.player.dash = True
                if e.type == KEYUP:
                    if e.key == K_RIGHT:
                        self.movement[1] = False
                    if e.key == K_LEFT:
                        self.movement[0] = False

            self.display.fill((61, 61, 89))

            self.scroll[0] += (self.player.rect.centerx - self.window_size[0]//2 - self.scroll[0])/20
            self.scroll[1] += (self.player.rect.centery - self.window_size[1]//2 - self.scroll[1])/20

            self.scroll[0] = max(0, min(self.scroll[0], 2016 - self.window_size[0]))
            # self.scroll[1] = max(0, min(self.scroll[1], 1000 - self.window_size[1]))

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            #update and render functions
            self.blit_ide_stuff(render_scroll)

            for spark in self.sparks:
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            self.tilemap.render(self.display, render_scroll)

            self.player.update(self.movement[1] - self.movement[0])
            self.player.render(self.display, render_scroll)

            for projectile in self.projectiles:
                if self.player.rect.colliderect(pg.Rect(projectile["pos"][0], projectile["pos"][1], self.projectile_size, self.projectile_size)) and not self.player.dash:
                    self.dead = True

            for wave in self.waves:
                if wave.check_death(self.player.rect.center, [self.player.rect.width, self.player.rect.height]) and not self.player.dash:
                    self.dead = True

                if wave.self_destruct:
                    self.waves.remove(wave)

                wave.update()
                wave.render(self.display, render_scroll)

            self.player.particle_system.update()

            if self.dead:
                self.dead_counter += 1

            if self.dead_counter >= 70:
                self.dead = False
                self.dead_counter = 0
                self.load_level()

            if self.dead_counter == 1:
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    self.sparks.append(Spark(self.player.rect.center, angle, 5 + random.random()))

            for enemy in self.enemies:
                if self.player.dash and self.player.rect.colliderect(enemy.rect):
                    enemy.self_destruct = True
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        self.sparks.append(Spark(self.player.rect.center, angle, 5 + random.random()))
                    self.sparks.append(Spark(self.player.rect.center, 0, 8 + random.random()))
                    self.sparks.append(Spark(self.player.rect.center, math.pi, 8 + random.random()))

                if enemy.self_destruct:
                    self.enemies.remove(enemy)

                enemy.check_walk(self.player.rect.centerx, self.player.rect.bottom)
                enemy.update(self.player.rect.center)
                enemy.render(self.display, render_scroll)

            if len(self.enemies) == 0 and len(self.tilemap.collidable_tiles) == 374:
                self.tilemap.collidable_tiles.popitem()

            self.clock.tick(60)
            pg.display.update()

if __name__ == "__main__":
    game = Game()
    game.run()
