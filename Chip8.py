import pygame
import numpy as np

import random
import os
import sys
import math

ZERO = bytes((0xF0, 0x90, 0x90, 0x90, 0xF0))
ONE = bytes((0x20, 0x60, 0x20, 0x20, 0x70))
TWO = bytes((0xF0, 0x10, 0xF0, 0x80, 0xF0))
THREE = bytes((0xF0, 0x10, 0xF0, 0x10, 0xF0))
FOUR = bytes((0x90, 0x90, 0xF0, 0x10, 0x10))
FIVE = bytes((0xF0, 0x80, 0xF0, 0x10, 0xF0))
SIX = bytes((0xF0, 0x80, 0xF0, 0x90, 0xF0))
SEVEN = bytes((0xF0, 0x10, 0x20, 0x40, 0x40))
EIGHT = bytes((0xF0, 0x90, 0xF0, 0x90, 0xF0))
NINE = bytes((0xF0, 0x90, 0xF0, 0x10, 0xF0))
A = bytes((0xF0, 0x90, 0xF0, 0x90, 0x90))
B = bytes((0xE0, 0x90, 0xE0, 0x90, 0xE0))
C = bytes((0xF0, 0x80, 0x80, 0x80, 0xF0))
D = bytes((0xE0, 0x90, 0x90, 0x90, 0xE0))
E = bytes((0xF0, 0x80, 0xF0, 0x80, 0xF0))
F = bytes((0xF0, 0x80, 0xF0, 0x80, 0x80))

class Chip8:
  def __init__(self, path):
    self.graphics = Graphics(800, 400)
    self.sound = Sound()
    self.cpu = Cpu()
    self.clock = pygame.time.Clock()
    self.sound_active = False
    self.load_rom(path)

  def load_rom(self, path):
    f =  open(path, "rb")
    b = os.path.getsize(path)
    self.cpu.memory[0x200 : 0x200 + b] = f.read()
    f.close()

  def run(self):
    for x in range (8):
      self.cpu.cycle()
    self.graphics.update(self.cpu.gfx)
    self.update_timers()
    self.clock.tick(60)

  def update_timers(self):
    if self.cpu.delay_timer > 0:
      self.cpu.delay_timer -= 1
    if self.cpu.sound_timer > 0:
      if(self.sound_active == False):
        self.sound.start()
        self.sound_active = True
      self.cpu.sound_timer -= 1
      if(self.cpu.sound_timer == 0):
        self.sound.stop()
        self.sound_active = False

class Cpu:
  def __init__(self):
    self.opcode = np.uint16(0)
    self.memory = bytearray(4096)
    self.V = bytearray(16)
    self.I = np.uint16(0)
    self.pc = np.uint16(0)
    self.pc = 0x200  
    self.gfx = bytearray(64 * 32 * 4)
    self.delay_timer = np.uint8(0)
    self.sound_timer = np.uint8(0)
    self.stack = np.zeros(16, dtype="uint16")
    self.sp = np.uint8(0)
    self.key = np.zeros(16, dtype="uint8")
    self.load_sprites()

  def load_sprites(self):
    self.memory[0x000 : 0x005] = ZERO
    self.memory[0x005 : 0x00A] = ONE
    self.memory[0x00A : 0x00F] = TWO
    self.memory[0x00F : 0x014] = THREE
    self.memory[0x014 : 0x019] = FOUR
    self.memory[0x019 : 0x01E] = FIVE
    self.memory[0x01E : 0x023] = SIX
    self.memory[0x023 : 0x028] = SEVEN
    self.memory[0x028 : 0x02D] = EIGHT
    self.memory[0x02D : 0x032] = NINE
    self.memory[0x032 : 0x037] = A
    self.memory[0x037 : 0x03C] = B
    self.memory[0x03C : 0x041] = C
    self.memory[0x041 : 0x046] = D
    self.memory[0x046 : 0x04B] = E
    self.memory[0x04B : 0x050] = F

  def draw_byte(self, byte, x, y):
    flag = 0
    p7 = byte & 0b00000001
    p6 = byte & 0b00000010
    p5 = byte & 0b00000100
    p4 = byte & 0b00001000
    p3 = byte & 0b00010000
    p2 = byte & 0b00100000
    p1 = byte & 0b01000000
    p0 = byte & 0b10000000

    if p0 > 0:
      flag += self.set_pixel_at(x, y)
    if p1 > 0:
      flag += self.set_pixel_at(x + 1, y)
    if p2 > 0:
      flag += self.set_pixel_at(x + 2, y)
    if p3 > 0:
      flag += self.set_pixel_at(x + 3, y)
    if p4 > 0:
      flag += self.set_pixel_at(x + 4, y)
    if p5 > 0:
      flag += self.set_pixel_at(x + 5, y)
    if p6 > 0:
      flag += self.set_pixel_at(x + 6, y)
    if p7 > 0:
      flag += self.set_pixel_at(x + 7, y)
    return 1 if flag > 0 else 0

  def set_pixel_at(self, x, y):
    offset = ((x + (y * 64)) * 4) & 0b1111111111111
    if self.gfx[offset] == 255:
      self.gfx[offset] = 0
      self.gfx[offset + 1] = 0
      self.gfx[offset + 2] = 0
      return 1
    else:
      self.gfx[offset] = 255
      self.gfx[offset + 1] = 255
      self.gfx[offset + 2] = 255
      return 0

  def cycle(self):
    # Fetch Opcode
    opcode = (self.memory[self.pc] << 8 | self.memory[self.pc + 1])

    # Decode Opcode
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    z = (opcode & 0x000F)
    kk = (opcode & 0x00FF)
    nnn = (opcode & 0x0FFF)

    #Clear the display.
    if opcode == 0x00E0:
      self.gfx.__init__(len(self.gfx))

    #Return from a subroutine.
    elif opcode == 0x00EE:
      self.pc = self.stack[self.sp]
      self.sp -= 1

    #Jump to location nnn.
    elif 0xFFF  < opcode and 0x2000 > opcode:
      self.pc = opcode & 0xFFF
      return

    #Call subroutine at nnn.
    elif  0x1FFF < opcode and 0x3000 > opcode:
      self.sp += 1
      self.stack[self.sp] = self.pc
      self.pc = opcode & 0xFFF
      return

    #Skip next instruction if Vx = kk.
    elif 0x2FFF < opcode and 0x4000 > opcode:
      if self.V[x] == kk:
        self.pc += 2

    #Skip next instruction if Vx != kk.
    elif 0x3FFF < opcode and 0x5000 > opcode:
      if self.V[x] != kk:
        self.pc += 2

    #Skip next instruction if Vx = Vy.
    elif 0x4FFF < opcode and 0x6000 > opcode:
      if self.V[x] == self.V[y]:
        self.pc += 2

    #Set Vx = kk.
    elif 0x5FFF < opcode and 0x7000 > opcode:
      self.V[x] = kk

    #Set Vx = Vx + kk.
    elif 0x6FFF < opcode and 0x8000 > opcode:
      self.V[x] = np.uint8(self.V[x] + kk)

    elif 0x7FFF < opcode and 0x9000 > opcode:
      if z == 0x0:
        self.V[x] = self.V[y]
      if z == 0x1:
        self.V[x] = self.V[x] | self.V[y]
      if z == 0x2:
        self.V[x] = self.V[x] & self.V[y]
      if z == 0x3:
        self.V[x] = self.V[x] ^ self.V[y]
      if z == 0x4:
        self.V[x] = np.uint8(self.V[x] + self.V[y])
        if (int(self.V[x]) + int(self.V[x])) > 255:
          self.V[0xF] = 1
        else:
          self.V[0xF] = 0
      if z == 5:
        if self.V[x] > self.V[y]:
          self.V[0xF] = 1
        else:
          self.V[0xF] = 0
        self.V[x] = np.uint8(self.V[x] - self.V[y])
      if z == 6:
        #least-significant bit of Vx
        if (self.V[x] & 0x80) == 1:
          self.V[0xF] = 1
        else:
          self.V[0xF] = 0
        self.V[x] //= 2
      if z == 7:
        if self.V[y] > self.V[x]:
          self.V[0xF] = 1
        else:
          self.V[0xF] = 0
        self.V[x] = np.uint8(self.V[y] - self.V[x])
      if z == 0xE:
        #most-significant bit of Vx
        if (self.V[x] & 1) == 1:
          self.V[0xF] = 1
        else:
          self.V[0xF] = 0
        self.V[x] = np.uint8(self.V[x] * 2)

    #Skip next instruction if Vx != Vy.
    elif 0x8FFF < opcode and 0xA000 > opcode:
      if self.V[x] != self.V[y]:
        self.pc += 2

    #Set I = nnn.
    elif 0x9FFF < opcode and 0xB000 > opcode:
      self.I = nnn

    #Jump to location nnn + V0.
    elif 0xAFFF < opcode and 0xC000 > opcode:
      self.pc = nnn + self.V[0]

    #Set Vx = random byte AND kk.
    elif 0xBFFF < opcode and 0xD000 > opcode:
      r = random.getrandbits(8)
      self.V[x] = np.uint8(kk & r)

    #Display z-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
    elif 0xCFFF < opcode and 0xE000 > opcode:
      flag = 0
      sprite = bytearray(z)
      sprite[0 : z] = self.memory [self.I : self.I + z]
      while z > 0:
        flag += self.draw_byte(self.memory[self.I + z - 1], self.V[x], self.V[y] + z - 1)
        z -= 1
      self.V[0xF] = 1 if flag > 0 else 0

    #keyboard
    elif 0xDFFF < opcode and 0xF000 > opcode:
      keyboard = pygame.key.get_pressed()
      key = 0
      if self.V[x] == 0x0:
        key = pygame.K_x
      elif self.V[x] == 0x1:
        key = pygame.K_1
      elif self.V[x] == 0x2:
        key = pygame.K_2
      elif self.V[x] == 0x3:
        key = pygame.K_3
      elif self.V[x] == 0x4:
        key = pygame.K_q
      elif self.V[x] == 0x5:
        key = pygame.K_w
      elif self.V[x] == 0x6:
        key = pygame.K_e
      elif self.V[x] == 0x7:
        key = pygame.K_a
      elif self.V[x] == 0x8:
        key = pygame.K_s
      elif self.V[x] == 0x9:
        key = pygame.K_d
      elif self.V[x] == 0xA:
        key = pygame.K_y
      elif self.V[x] == 0xB:
        key = pygame.K_c
      elif self.V[x] == 0xC:
        key = pygame.K_4
      elif self.V[x] == 0xD:
        key = pygame.K_r
      elif self.V[x] == 0xE:
        key = pygame.K_f
      elif self.V[x] == 0xF:
        key = pygame.K_v

      if kk == 0x9E:
        if keyboard[key] == True:
          self.pc += 2
      
      elif kk == 0xA1:
        if keyboard[key] == False:
          self.pc += 2

    else:
      if kk == 0x07:
        self.V[x] = self.delay_timer
      elif kk == 0x0A:
        keyboard = pygame.key.get_pressed()
        if keyboard[pygame.K_x] == True:
          self.V[x] = 0x0
        elif keyboard[pygame.K_1] == True:
           self.V[x] = 0x1
        elif keyboard[pygame.K_2] == True:
           self.V[x] = 0x2
        elif keyboard[pygame.K_3] == True:
          self.V[x] = 0x3
        elif keyboard[pygame.K_q] == True:
          self.V[x] = 0x4
        elif keyboard[pygame.K_w] == True:
          self.V[x] = 0x5
        elif keyboard[pygame.K_e] == True:
          self.V[x] = 0x6
        elif keyboard[pygame.K_a] == True:
          self.V[x] = 0x7
        elif keyboard[pygame.K_s] == True:
          self.V[x] = 0x8
        elif keyboard[pygame.K_d] == True:
          self.V[x] = 0x9
        elif keyboard[pygame.K_y] == True:
          self.V[x] = 0xA
        elif keyboard[pygame.K_c] == True:
          self.V[x] = 0xB
        elif keyboard[pygame.K_4] == True:
          self.V[x] = 0xC
        elif keyboard[pygame.K_r] == True:
          self.V[x] = 0xD
        elif keyboard[pygame.K_f] == True:
          self.V[x] = 0xE
        elif keyboard[pygame.K_v] == True:
          self.V[x] = 0xF
        else:
          return

      elif kk == 0x15:
        self.delay_timer = self.V[x]
      elif kk == 0x18:
        self.sound_timer = self.V[x]
      elif kk == 0x1E:
        self.I = self.I + self.V[x]
      elif kk == 0x29:
        if(self.V[x] == 0x0):
          self.I = 0x000
        if(self.V[x] == 0x1):
          self.I = 0x005
        if(self.V[x] == 0x2):
          self.I = 0x00A
        if(self.V[x] == 0x3):
          self.I = 0x00F
        if(self.V[x] == 0x4):
          self.I = 0x014
        if(self.V[x] == 0x5):
          self.I = 0x019
        if(self.V[x] == 0x6):
          self.I = 0x01E
        if(self.V[x] == 0x7):
          self.I = 0x023
        if(self.V[x] == 0x8):
          self.I = 0x028
        if(self.V[x] == 0x9):
          self.I = 0x02D
        if(self.V[x] == 0xA):
          self.I = 0x032
        if(self.V[x] == 0xB):
          self.I = 0x037
        if(self.V[x] == 0xC):
          self.I = 0x03C
        if(self.V[x] == 0xD):
          self.I = 0x041
        if(self.V[x] == 0xE):
          self.I = 0x046
        if(self.V[x] == 0xF):
          self.I = 0x04B
      elif kk == 0x33:
        hundreds = math.floor(self.V[x] / 100)
        tens = (math.floor(self.V[x] / 10)) % 10
        ones = (self.V[x] % 100) % 10
        self.memory[self.I] = np.uint8(hundreds)
        self.memory[self.I + 1] = np.uint8(tens)
        self.memory[self.I + 2] = np.uint8(ones)
      elif kk == 0x55:
        for i in range (x + 1):
          self.memory[self.I + i] = self.V[i]
      elif kk == 0x65:
        for i in range (x + 1):
          self.V[i] = self.memory[self.I + i]  

    self.pc += 2

class Graphics:
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.c8surface = pygame.Surface((64, 32))
    pygame.display.set_caption("Chip8")
    pygame.display.set_icon(self.c8surface)
    self.c8display = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

  def resize(self, width, height):
    self.width = width
    self.height = height
    self.c8display = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

  def update(self, array):
    self.c8surface.get_buffer().write(bytes(array))
    displaysurface = pygame.transform.scale(self.c8surface, (self.width, self.height))
    self.c8display.blit(displaysurface, (0, 0))
    pygame.display.update()

  def clear(self):
    self.c8surface.fill((255, 255, 255))

class Sound:
  def __init__(self):
    path = "./beep.wav"
    self.enabled = True
    if os.path.isfile(path):
      self.effect = pygame.mixer.Sound(path)
    else:
      self.enabled = False
      print("sound file \"beep.wav\" not found, continuing without sound")

  def start(self):
    if self.enabled:
      self.effect.play(-1)

  def stop(self):
    if self.enabled:
      self.effect.stop()

def main():
    # read command line argument
    if len(sys.argv) > 1:
      path = sys.argv[1]
    else:
      print("error: no input file")
      return

    pygame.init()
    random.seed()
    chip8 = Chip8(path)

    # define a variable to control the main loop
    running = True

    # main loop
    while running:
      chip8.run()
      # event handling, gets all event from the event queue
      for event in pygame.event.get():
          if event.type == pygame.VIDEORESIZE:
            chip8.graphics.resize(event.w, event.h)
          if event.type == pygame.QUIT:
              running = False


if __name__ == '__main__':
    main()
