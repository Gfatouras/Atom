import pygame
import random
import math
import numpy as np
from collections import defaultdict

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 200, 200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nuclear Decay Simulation")

# Colors
BLACK = (0, 0, 0)
RED = (255, 50, 50)    # Protons
BLUE = (100, 100, 255) # Neutrons
GREEN = (50, 255, 50)  # Electrons (β⁻)
PINK = (255, 100, 255) # Positrons (β⁺)
WHITE = (255, 255, 255)

# Nucleon properties
NUCLEON_RADIUS = 2
FRAGMENT_DISTANCE = 100

# Physics parameters
STRONG_FORCE_RADIUS = 30
ELECTROSTATIC_CONSTANT = 40
STRONG_FORCE_CONSTANT = 10
MAX_VELOCITY = 2
SPRING_DAMPENING = 0.3

# Decay parameters
BETA_DECAY_PROBABILITY = 0.002
NEUTRON_RICH_THRESHOLD = 1.5
PROTON_RICH_THRESHOLD = 1.2

# Particle counts
INITIAL_PROTONS = 12
INITIAL_NEUTRONS = 16

class Nucleon:
    def __init__(self, x, y, is_proton):
        self.is_proton = is_proton  # Fixed typo in variable name
        self.pos = np.array([float(x), float(y)])
        self.vel = np.array([random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)])
        self.color = RED if is_proton else BLUE
        self.fragment_id = 0
        self.bond_strength = 0

    def update(self, nucleons):
        self.calculate_neighbors(nucleons)
        self.apply_forces(nucleons)
        self.move()
        return self.check_decay(nucleons)

    def apply_forces(self, nucleons):
        for other in nucleons:
            if other is not self:
                if self.is_proton and other.is_proton:
                    self.electrostatic_force(other)
                self.strong_force(other)

    def electrostatic_force(self, other):
        delta = other.pos - self.pos
        distance = max(np.linalg.norm(delta), 0.1)
        if distance < 100:
            force = (ELECTROSTATIC_CONSTANT / (distance**2 + 1)) * delta/distance
            self.vel -= force * 0.5
            other.vel += force * 0.5

    def strong_force(self, other):
        delta = other.pos - self.pos
        distance = max(np.linalg.norm(delta), 0.1)
        
        if distance < STRONG_FORCE_RADIUS:
            if distance < 8:
                force = -STRONG_FORCE_CONSTANT * (8 - distance) * delta/distance
            elif distance < 20:
                force = STRONG_FORCE_CONSTANT * math.exp(-distance/5) * delta/distance
            else:
                force = np.array([0, 0])
            
            self.vel += force * 0.5
            other.vel -= force * 0.5
            
            rel_vel = other.vel - self.vel
            damping = SPRING_DAMPENING * (1 - distance/STRONG_FORCE_RADIUS) * rel_vel
            self.vel += damping
            other.vel -= damping

    def move(self):
        self.pos += self.vel
        # Wrap around edges
        self.pos[0] %= WIDTH
        self.pos[1] %= HEIGHT

    def calculate_neighbors(self, nucleons):
        self.neighbors = 0
        self.bond_strength = 0
        for other in nucleons:
            if other is not self:
                distance = np.linalg.norm(other.pos - self.pos)
                if distance < STRONG_FORCE_RADIUS:
                    self.neighbors += 1
                    if distance < 15:
                        self.bond_strength += (15 - distance)

    def check_decay(self, nucleons):
        if random.random() > BETA_DECAY_PROBABILITY:
            return None
        
        fragment_nucleons = [n for n in nucleons if n.fragment_id == self.fragment_id]
        protons = sum(1 for n in fragment_nucleons if n.is_proton)
        neutrons = len(fragment_nucleons) - protons
        
        if neutrons == 0 and protons == 0:
            return None
        
        # Beta-minus decay
        if (not self.is_proton and neutrons > 0 and 
            (protons == 0 or neutrons/protons > NEUTRON_RICH_THRESHOLD) and 
            self.bond_strength < 20):
            
            self.is_proton = True  # Fixed variable name
            self.color = RED
            print(f"β⁻ decay: n→p (n/p={neutrons}/{protons})")
            return {"pos": self.pos.copy(), "type": "electron"}
        
        # Beta-plus decay
        elif (self.is_proton and protons > 0 and 
              (neutrons == 0 or protons/neutrons > PROTON_RICH_THRESHOLD) and 
              self.bond_strength < 15):
            
            self.is_proton = False
            self.color = BLUE
            print(f"β⁺ decay: p→n (p/n={protons}/{neutrons})")
            return {"pos": self.pos.copy(), "type": "positron"}
        
        return None

class DecayEffect:
    def __init__(self, pos):
        self.pos = pos
        self.lifetime = 1
        self.radius = NUCLEON_RADIUS * 5
        
    def draw(self, screen):
        if self.lifetime > 0:
            for r in range(self.radius, 0, -1):
                alpha = int(255 * (r/self.radius))
                color = (255, 255, 255, alpha)
                pygame.draw.circle(screen, color, self.pos.astype(int), r)
            self.lifetime -= 1

def detect_fragments(nucleons):
    """Identify separate clusters using connected components"""
    if not nucleons:
        return []
    
    n = len(nucleons)
    adj = np.zeros((n, n), dtype=bool)
    
    for i in range(n):
        for j in range(i+1, n):
            distance = np.linalg.norm(nucleons[i].pos - nucleons[j].pos)
            if distance < STRONG_FORCE_RADIUS * 0.7:
                adj[i][j] = adj[j][i] = True
                
    visited = [False] * n
    components = []
    
    for i in range(n):
        if not visited[i]:
            stack = [i]
            visited[i] = True
            component = [i]
            
            while stack:
                node = stack.pop()
                for neighbor in range(n):
                    if adj[node][neighbor] and not visited[neighbor]:
                        visited[neighbor] = True
                        stack.append(neighbor)
                        component.append(neighbor)
            
            components.append(component)
    
    return components

# Initialize simulation
nucleons = []
for i in range(INITIAL_PROTONS + INITIAL_NEUTRONS):
    angle = random.uniform(0, 2*math.pi)
    r = random.uniform(0, 20)
    x = WIDTH//2 + r * math.cos(angle)
    y = HEIGHT//2 + r * math.sin(angle)
    is_proton = (i < INITIAL_PROTONS)
    nucleons.append(Nucleon(x, y, is_proton))

decay_effects = []
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 16)
show_fragments = False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                show_fragments = not show_fragments
            elif event.key == pygame.K_r:
                nucleons = []
                for i in range(INITIAL_PROTONS + INITIAL_NEUTRONS):
                    angle = random.uniform(0, 2*math.pi)
                    r = random.uniform(0, 20)
                    x = WIDTH//2 + r * math.cos(angle)
                    y = HEIGHT//2 + r * math.sin(angle)
                    is_proton = (i < INITIAL_PROTONS)
                    nucleons.append(Nucleon(x, y, is_proton))
                decay_effects = []

    screen.fill(BLACK)
    
    # Update fragments
    fragments = detect_fragments(nucleons)
    for frag_id, fragment in enumerate(fragments):
        for n_idx in fragment:
            nucleons[n_idx].fragment_id = frag_id
    
    # Update nucleons and check for decays
    for nucleon in nucleons:
        decay_result = nucleon.update(nucleons)
        if decay_result:
            decay_effects.append(DecayEffect(decay_result["pos"]))
    
    # Draw bonds
    for i, n1 in enumerate(nucleons):
        for n2 in nucleons[i+1:]:
            distance = np.linalg.norm(n1.pos - n2.pos)
            if distance < STRONG_FORCE_RADIUS:
                if show_fragments:
                    if n1.fragment_id == n2.fragment_id:
                        color = (100, 100, 255) if n1.fragment_id == 0 else (255, 100, 100)
                    else:
                        color = (200, 200, 200)
                else:
                    alpha = min(255, int(255 * (1 - distance/STRONG_FORCE_RADIUS)))
                    color = (100, 100, 100, alpha)
                pygame.draw.line(screen, color, n1.pos.astype(int), n2.pos.astype(int), 1)
    
    # Draw decay effects
    for effect in decay_effects[:]:
        effect.draw(screen)
        if effect.lifetime <= 0:
            decay_effects.remove(effect)
    
    # Draw nucleons
    for nucleon in nucleons:
        if show_fragments:
            frag_color = (100, 100, 255) if nucleon.fragment_id == 0 else (255, 100, 100)
            pygame.draw.circle(screen, frag_color, nucleon.pos.astype(int), NUCLEON_RADIUS + 1)
        pygame.draw.circle(screen, nucleon.color, nucleon.pos.astype(int), NUCLEON_RADIUS)
        if nucleon.is_proton:
            pygame.draw.circle(screen, WHITE, nucleon.pos.astype(int), NUCLEON_RADIUS//2)
    
    # Display info
    protons = sum(1 for n in nucleons if n.is_proton)
    neutrons = len(nucleons) - protons
    info_text = [
        f"Protons: {protons}  Neutrons: {neutrons}  n/p: {neutrons/max(1,protons):.2f}",
        f"Fragments: {len(fragments)}",
        "F: Toggle fragments  R: Reset"
    ]
    for i, text in enumerate(info_text):
        text_surface = font.render(text, True, WHITE)
        screen.blit(text_surface, (10, 10 + i*20))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()