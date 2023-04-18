import sys
import pygame
from numpy import uint8, uint16, unpackbits

class Chip8:
    def __init__(self, path: str):
        pygame.init()
        self.screen = pygame.display.set_mode((64,32), pygame.RESIZABLE)
        self.memory = [uint8(0)] * 4096
        self.pc = uint16(0x200)
        self.i = uint16(0)
        self.sp = uint16(0)
        self.delay_timer = uint8(0)
        self.sound_timer = uint8(0)
        self.regs = [uint8(0)] * 0x10
        self.display = [0] * 32 * 64
        # This is font data I took from this website:
        # https://tobiasvl.github.io/blog/write-a-chip-8-emulator/
        for index, char in enumerate(
        [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
        0x20, 0x60, 0x20, 0x20, 0x70, # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
        0x90, 0x90, 0xF0, 0x10, 0x10, # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
        0xF0, 0x10, 0x20, 0x40, 0x40, # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90, # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
        0xF0, 0x80, 0x80, 0x80, 0xF0, # C
        0xE0, 0x90, 0x90, 0x90, 0xE0, # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
        0xF0, 0x80, 0xF0, 0x80, 0x80]):  # F
            self.memory[0x50 + index] = uint8(char)
        
        # Load the file
        try:
            load_address = 0x200
            with open(path, 'rb') as f:
                while byte := f.read(1):
                    self.memory[load_address] = uint8(int.from_bytes(byte, byteorder='big'))
                    load_address += 1
        except Exception as e:
            print(e)
            print("Error occurred while opening file")
            sys.exit(-1)
    
    def draw(self):
        black = (0,0,0)
        white = (255,255,255)
        self.screen.fill(black)
        for y in range(32):
            for x in range(64):
                pixel = self.display[x + y * 64]
                if pixel == 1:
                    pygame.draw.rect(self.screen, white, (x, y, 1, 1))
        pygame.display.update()


    def execute(self):
        ins = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        header = (ins & 0xF000) >> 12
        match header:
            case 0x0:
                # Clear screen
                if ins == 0x00E0:
                    self.display = [0] * 32 * 64
            case 0x1:
                # Jump
                self.pc = ins & 0x0FFF
            case 0x6:
                # Set register VX
                self.regs[(ins & 0x0F00) >> 8] = ins & 0x00FF
            case 0x7:
                # Add register VX
                self.regs[(ins & 0x0F00) >> 8] += ins & 0x00FF
            case 0xA:
                # Set index register
                self.i = ins & 0x0FFF
            case 0xD:
                # Display instruction
                x = self.regs[(ins & 0x0F00) >> 8]
                y = self.regs[(ins & 0x00F0) >> 4]
                # The number of vertical rows this sprite contains
                n = ins & 0x000F
                # Reset the collision flag
                self.regs[0xF] = 0
                # Begin drawing
                for line in range(n):
                    pixel_position = x + (y + line) * 64
                    horizonal_row_data = self.memory[self.i + line]
                    for x_offset, pixel in enumerate(unpackbits(horizonal_row_data)):
                        if pixel_position + x_offset > len(self.display):
                            break
                        if pixel == 1:
                            if self.display[pixel_position + x_offset] == 1:
                                # Set the collision flag to 1
                                self.regs[0xF] = 1
                            self.display[pixel_position + x_offset] ^= 1
                self.draw()



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: chip8.py PATH_TO_CHIP8_ROM")
        sys.exit(-1)
    chip8 = Chip8(sys.argv[1])
    while True:
        chip8.execute()