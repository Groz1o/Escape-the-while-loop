import pygame as pg
import random

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.randint(2, 5)
        self.color = (255, 255, 0)
        self.x_velocity = random.uniform(-1, 1)
        self.y_velocity = random.uniform(-1, 1)
        self.life = random.randint(20, 40)

    def update(self):
        self.x += self.x_velocity
        self.y += self.y_velocity
        self.radius = max(0, self.radius - 0.1)
        self.life -= 1

    def draw(self, surface, offset):
        if self.radius > 0:
            pg.draw.circle(surface, self.color, (int(self.x) - offset[0], int(self.y) - offset[1]), int(self.radius))

    def is_dead(self):
        return self.life <= 0

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y):
        for _ in range(5):
            self.particles.append(Particle(x, y))

    def update(self):
        self.particles = [particle for particle in self.particles if not particle.is_dead()]
        for particle in self.particles:
            particle.update()

    def draw(self, surface, offset):
        for particle in self.particles:
            particle.draw(surface, offset)