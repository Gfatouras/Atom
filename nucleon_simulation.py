import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 200, 200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nucleon Simulation")

# Colors
BLACK = (20, 20, 20)
RED = (255, 0, 0)  # Protons
BLUE = (50, 50, 255)  # Neutrons

# Nucleon properties
NUCLEON_RADIUS = 2  # Approx. 0.84 fm scaled to simulation units

STRONG_FORCE_RADIUS = 30
ELECTROSTATIC_CONSTANT = 80  # Simplified constant for repulsion
ELECTROSTATIC_RADIUS = 50  # Radius where repulsion is zero
STRONG_FORCE_CUTOFF = 0.001  # Fraction of maximum force
STRONG_FORCE_CONSTANT = 10  # Simplified constant for strong nuclear force
MAX_VELOCITY = 5  # Maximum velocity for nucleons

# Spring dampening global variable
SPRING_DAMPENING = 0.2  # Controls the strength of velocity damping

# Update global variables for protons and neutrons
NUM_PROTONS = 12
NUM_NEUTRONS = 6

# Nucleon class
class Nucleon:
    def __init__(self, x, y, charge):
        # Remove randomness from nucleon type assignment
        self.nucleon = charge  # 0 = Neutron, 1 = Proton
        self.charge = self.nucleon
        self.posX = x
        self.posY = y
        self.velX = random.uniform(-1, 1)
        self.velY = random.uniform(-1, 1)
        self.color = RED if self.charge == 1 else BLUE
        self.neighbors = 0  # Initialize neighbors count

    def enforce_max_velocity(self):
        # Enforce maximum velocity
        speed = math.sqrt(self.velX**2 + self.velY**2)
        if speed > MAX_VELOCITY:
            scale = MAX_VELOCITY / speed
            self.velX *= scale
            self.velY *= scale

    def move(self):
        # Enforce maximum velocity before moving
        self.enforce_max_velocity()

        self.posX += self.velX
        self.posY += self.velY

        # Bounce off walls
        if self.posX < 0 or self.posX > WIDTH:
            self.velX *= -1
        if self.posY < 0 or self.posY > HEIGHT:
            self.velY *= -1
            
        # Validate positions
        if not math.isfinite(self.posX) or not math.isfinite(self.posY):
            self.posX, self.posY = WIDTH // 2, HEIGHT // 2  # Reset to center
            
    def repulsion(self, other):
        if self.nucleon == 1 and other.nucleon == 1:  # Only protons repel
            dx = other.posX - self.posX
            dy = other.posY - self.posY
            distance = max(math.sqrt(dx**2 + dy**2), 1e-5)  # Clamp distance to prevent division by zero

            if distance < ELECTROSTATIC_RADIUS:
                # Inverse-square law for repulsion
                force = ELECTROSTATIC_CONSTANT / (distance**2)
                fx = force * (dx / distance)
                fy = force * (dy / distance)

                # Apply forces
                self.velX -= fx
                self.velY -= fy
                other.velX += fx
                other.velY += fy

    def strong_force(self, other):
        dx = other.posX - self.posX
        dy = other.posY - self.posY
        distance = max(math.sqrt(dx**2 + dy**2), 1e-5)  # Clamp distance to prevent division by zero

        if distance < STRONG_FORCE_RADIUS:
            # Exponential decay for the strong nuclear force
            if distance < 10:  # Very close range: repulsive strong force
                force = STRONG_FORCE_CONSTANT * math.exp(-distance / 2) * -1  # Repulsion
            elif distance < 20:  # Medium range: attractive strong force
                force = STRONG_FORCE_CONSTANT * math.exp(-distance / 2)  # Attraction
            else:  # Beyond strong force range
                force = 0

            fx = force * (dx / distance)
            fy = force * (dy / distance)

            # Apply forces
            self.velX += fx
            self.velY += fy
            other.velX -= fx
            other.velY -= fy

            # Calculate relative velocity and apply damping
            rel_vel_x = other.velX - self.velX
            rel_vel_y = other.velY - self.velY
            rel_vel_magnitude = math.sqrt(rel_vel_x**2 + rel_vel_y**2)

            damping_x = SPRING_DAMPENING * rel_vel_magnitude * (dx / distance)
            damping_y = SPRING_DAMPENING * rel_vel_magnitude * (dy / distance)

            self.velX += damping_x
            self.velY += damping_y
            other.velX -= damping_x
            other.velY -= damping_y

    # Add a method to calculate the number of neighbors (bonds) for each nucleon
    def calculate_neighbors(self, all_nucleons):
        self.neighbors = 0
        for other in all_nucleons:
            if other is not self:
                dx = other.posX - self.posX
                dy = other.posY - self.posY
                distance = math.sqrt(dx**2 + dy**2)
                if distance < STRONG_FORCE_RADIUS:  # Within bonding range
                    self.neighbors += 1

    def decay(self):
        pass  # Decay logic removed as per request

# Update nucleon creation to spawn exactly NUM_PROTONS protons and NUM_NEUTRONS neutrons without randomness
nucleons = []
for i in range(NUM_PROTONS):
    x = (i % 5) * (WIDTH // 5) + (WIDTH // 10)  # Distribute protons evenly
    y = (i // 5) * (HEIGHT // 5) + (HEIGHT // 10)
    nucleons.append(Nucleon(x, y, 1))  # Proton
for i in range(NUM_NEUTRONS):
    x = (i % 5) * (WIDTH // 5) + (WIDTH // 10)  # Distribute neutrons evenly
    y = (i // 5) * (HEIGHT // 5) + (HEIGHT // 10)
    nucleons.append(Nucleon(x, y, 0))  # Neutron

clock = pygame.time.Clock()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:  # Increase velocity by 10%
                for nucleon in nucleons:
                    nucleon.velX *= 1.1
                    nucleon.velY *= 1.1
            elif event.key == pygame.K_DOWN:  # Decrease velocity by 10%
                for nucleon in nucleons:
                    nucleon.velX *= 0.9
                    nucleon.velY *= 0.9

    # Clear screen
    screen.fill(BLACK)

    # Update and draw nucleons
    for i, nucleon in enumerate(nucleons):
        nucleon.calculate_neighbors(nucleons)  # Calculate neighbors for each nucleon
        for j, other in enumerate(nucleons):
            if i != j:  # Ensure it's not the same nucleon
                nucleon.repulsion(other)
                nucleon.strong_force(other)  # Apply strong nuclear force

                # Draw faint lines if nucleons are more attracted than repulsed
                dx = other.posX - nucleon.posX
                dy = other.posY - nucleon.posY
                distance = max(math.sqrt(dx**2 + dy**2), 1e-5)
                if distance < STRONG_FORCE_RADIUS and distance >= 10:
                    pygame.draw.line(screen, (100, 100, 100), (nucleon.posX, nucleon.posY), (other.posX, other.posY), 1)

        nucleon.move()
        pygame.draw.circle(screen, nucleon.color, (int(nucleon.posX), int(nucleon.posY)), NUCLEON_RADIUS)

    # Update display
    pygame.display.flip()

    # Cap the frame rate at 60 FPS
    clock.tick(60)

# Clean up
pygame.quit()


