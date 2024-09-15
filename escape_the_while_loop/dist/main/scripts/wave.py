import pygame as pg

class Wave:
    def __init__(self, enemy_pos):
        self.enemy_pos = enemy_pos
        self.wave_radius = 0
        self.wave_speed = 2
        self.self_destruct = False

    def check_death(self, player_pos, player_size):
        tolerance = 5

        player_center_x = player_pos[0] + player_size[0] // 2
        player_center_y = player_pos[1] + player_size[1] // 2
        distance_to_center = ((self.enemy_pos[0] - player_center_x) ** 2 + (self.enemy_pos[1] - player_center_y) ** 2) ** 0.5

        return abs(distance_to_center - self.wave_radius) <= tolerance

    def update(self):
        self.wave_radius = min(200, self.wave_radius + self.wave_speed)
        if self.wave_radius >= 200:
            self.self_destruct = True

    def render(self, display, offset):
        pg.draw.circle(display, "blue", (self.enemy_pos[0] - offset[0], self.enemy_pos[1] - offset[1]), self.wave_radius, 2)
