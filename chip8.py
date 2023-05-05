import sys
from typing import Union
import pygame
from numpy import uint8, uint16, unpackbits
import secrets
from time import sleep
import multiprocessing

width = 64
height = 32


class Chip8:
    # width = 640
    def __init__(self, path: str):
        pygame.init()
        self.screen = pygame.Surface((width, height))
        # self.screen = pygame.display.set_mode(
        #     (width, height), pygame.RESIZABLE)

        self.windisplay = pygame.display.set_mode(
            (width * 16, height * 16), pygame.RESIZABLE)
        self.memory = [uint8(0)] * 4096
        self.pc = uint16(0x200)
        self.i = uint16(0)
        self.sp = uint16(4095)
        self.delay_timer = uint8(0)
        self.sound_timer = uint8(0)
        self.regs = [uint8(0)] * 0x10
        self.display = [0] * width * height
        self.pressed_key: uint8 = 0x0  # Keys are 0-F

        # This is font data I took from this website:
        # https://tobiasvl.github.io/blog/write-a-chip-8-emulator/
        for index, char in enumerate(
            [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
             0x20, 0x60, 0x20, 0x20, 0x70,  # 1
             0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
             0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
             0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
             0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
             0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
             0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
             0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
             0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
             0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
             0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
             0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
             0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
             0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
             0xF0, 0x80, 0xF0, 0x80, 0x80]):  # F
            self.memory[0x50 + index] = uint8(char)

        # Load the file
        try:
            load_address = 0x200
            with open(path, 'rb') as f:
                while byte := f.read(1):
                    self.memory[load_address] = uint8(
                        int.from_bytes(byte, byteorder='big'))
                    load_address += 1
        except Exception as e:
            print(e)
            print("Error occurred while opening file")
            sys.exit(-1)

    @staticmethod
    def grabxandy(instruction: uint16) -> Union[int, int]:
        # x is the second nibble and y is in the third nibble
        return ((instruction & 0xF00) >> 8, (instruction & 0xF0) >> 4)

    def starttimer(self, time, isdelaytimer: bool = True):
        def startdelaytimer():
            def tick():
                sleep(1/60)
                self.delay_timer -= 1
            self.delay_timer = time
            while self.delay_timer > 0:
                tick()

        def startsoundtimer():
            def tick():
                sleep(1/60)
                self.sound_timer -= 1
            self.sound_timer = time
            while self.sound_timer > 0:
                tick()
        # start

        if isdelaytimer:
            multiprocessing.Process(target=startdelaytimer)
        else:
            multiprocessing.Process(target=startsoundtimer)

    # def startdelaytimer(self, time):
    #     def tick():
    #         sleep(1/60)
    #         self.delay_timer -= 1
    #     self.delay_timer = time
    #     while self.delay_timer > 0:
    #         tick()

    def draw(self):
        black = (0, 0, 0)
        white = (255, 255, 255)
        self.screen.fill(black)
        for y in range(32):
            for x in range(64):
                pixel = self.display[x + y * 64]
                if pixel == 1:
                    pygame.draw.rect(self.screen, white, (x, y, 1, 1))
        scaled_win = pygame.transform.smoothscale(
            self.screen, self.windisplay.get_size())
        self.windisplay.blit(scaled_win, (0, 0))
        pygame.display.flip()
        pygame.display.update()

    def grabpressedkey(self) -> int:
        keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r,
                pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f,
                pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v]
        pressedkeys = pygame.key.get_pressed()
        for i, key in enumerate(keys):
            if pressedkeys[key]:
                return (i)
        return 0x0

    def execute(self):
        # print(self.pc)
        ins = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        print(hex(ins))
        self.pc += 2
        header = (ins & 0xF000) >> 12

        match header:
            case 0x0:
                match ins:
                    case 0x00E0:
                        # Clear screen
                        self.display = [0] * 32 * 64
                    case 0x00EE:
                        # stack pop
                        self.sp += 2
                        self.pc = self.memory[self.sp -
                                              1] << 8 | self.memory[self.sp]
                    case _:
                        raise Exception(f"Invalid key: {hex(ins)}")
            case 0x1:
                # Jump
                self.pc = ins & 0x0FFF
            case 0x2:
                # function call
                # push pc to stack and jump

                self.sp -= 2    # decrement stack
                self.memory[self.sp + 2] = self.pc & 0x00FF  # save pc
                self.memory[self.sp + 1] = self.pc & 0xFF00
            case 0x3:
                # skip if equals
                (x, _) = Chip8.grabxandy(ins)

                nn = ins & 0x00FF
                if self.regs[x] == nn:
                    self.pc += 2
            case 0x4:
                (x, _) = Chip8.grabxandy(ins)

                nn = ins & 0x00FF
                if self.regs[x] != nn:
                    self.pc += 2

            case 0x5:
                # skip if equals
                (x, y) = Chip8.grabxandy(ins)
                if self.regs[x] == self.regs[y]:
                    self.pc += 2

            case 0x6:
                # Set register VX
                self.regs[(ins & 0x0F00) >> 8] = ins & 0x00FF
            case 0x7:
                # Add register VX
                self.regs[(ins & 0x0F00) >> 8] += ins & 0x00FF
            case 0x8:
                # logical operations
                # instructions are in the form 0x8XYi
                # for i in 0..16
                (x, y) = Chip8.grabxandy(ins)
                match ins & 0xF:
                    case 0x0:
                        # set x = y
                        self.regs[x] = self.regs[y]
                    case 0x1:
                        # Binary OR
                        self.regs[x] = self.regs[x] | self.regs[y]
                    case 0x2:
                        # Binary AND
                        self.regs[x] = self.regs[x] & self.regs[y]
                    case 0x3:
                        # Logical XOR
                        self.regs[x] = self.regs[x] ^ self.regs[y]
                    case 0x4:
                        # Add instruction, records overflow
                        if (self.regs[x] + self.regs[y] > 255):
                            self.regs[0xf] = 1
                        else:
                            self.regs[0xf] = 0
                        self.regs[x] = self.regs[x] + self.regs[y]
                    case 0x5:
                        # substraction, vx = vx - vy
                        self.regs[0xf] = 1
                        self.regs[x] = self.regs[x] - self.regs[y]
                        if self.regs[y] > self.regs[x]:
                            self.regs[0xf] = 0
                    case 0x6:
                        # set and shift right. lost bit saved in 0xf
                        self.regs[0xf] = self.regs[y] << 15
                        self.regs[x] = self.regs[y] >> 1
                    case 0x7:
                        # subtraction.  vs = vy - vx
                        self.regs[0xf] = 1
                        self.regs[x] = self.regs[y] - self.regs[x]
                        if self.regs[x] > self.regs[y]:
                            self.regs[0xf] = 0
                    case 0xE:
                        # set and shift left. lost bit saved in 0xf
                        self.regs[0xf] = self.regs[y] >> 15
                        self.regs[x] = self.regs[y] << 1
                    case _:
                        raise Exception(f"Invalid key {hex(ins)}")
            case 0x9:
                # skip if not equals
                (x, y) = Chip8.grabxandy(ins)
                if self.regs[x] != self.regs[y]:
                    self.pc += 2
            case 0xA:
                # Set index register
                self.i = ins & 0x0FFF
            case 0xB:
                # I will be implementing the COSMAC VIP version here
                # what this does is given BNNN instruction
                # it jumps to NNN + the value in v0
                self.pc = self.regs[0x0] + (ins & 0xFFF)
            case 0xC:
                # generates a random number an ANDS it to NN from C
                # put the result in X
                rand = secrets.randbits(16)
                (x, _) = Chip8.grabxandy(ins)
                self.regs[x] = uint16(rand) & (0x00FF & ins)
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
            case 0xE:
                # There are two versions.
                # EX9E checks if the key is vx is pressed. if so skip
                # EXA1 checks if the key in vx is not pressed. if so skip
                match (ins & 0xFF):
                    case 0x9E:
                        if self.regs[(ins & 0x0F00) >> 8] == self.pressed_key:
                            self.pc += 2
                    case 0xA1:
                        if self.regs[(ins & 0x0F00) >> 8] != self.pressed_key:
                            self.pc += 2
                    case _:
                        raise Exception(f"Invalid key {hex(ins)}")
            case 0xF:
                # manipulates timers
                (x, _) = self.grabxandy(ins)
                match (ins & 0xFF):
                    case 0x07:
                        self.regs[x] = self.delay_timer
                    case 0x0A:
                        key = self.grabpressedkey()
                        if key == 0x0:
                            # no key pressed
                            self.pc -= 2
                        else:
                            self.regs[x] = key

                    case 0x15:
                        delay = self.regs[x]
                        self.starttimer(delay)
                    case 0x18:
                        delay = self.regs[x]
                        self.starttimer(delay, isdelaytimer=False)
                    case 0x1E:

                        self.i += self.regs[x]
                        if self.i > 0x0FFF:
                            self.regs[0xf] = 1
                    case 0x29:
                        character = self.regs[x] & 0xF
                        fontaddr = 0x50
                        offset = character * 5
                        self.i = fontaddr + offset
                    case 0x33:
                        number = self.regs[x]
                        first, second, third = (
                            number / 100) % 10, (number / 10) % 10, number % 10
                        self.memory[self.i] = first
                        self.memory[self.i + 1] = second
                        self.memory[self.i + 2] = third
                    case 0x55:
                        for i in range(0, x + 1):
                            self.memory[self.i + i] = self.regs[i]
                    case 0x65:
                        for i in range(0, x + 1):
                            self.regs[i] = self.memory[self.i + i]
                    case _:
                        raise Exception(f"Invalid key {hex(ins)}")
            case _:
                raise Exception(f"Invalid key {hex(ins)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: chip8.py PATH_TO_CHIP8_ROM")
        sys.exit(-1)
    chip8 = Chip8(sys.argv[1])

    while True:
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        chip8.execute()
        sleep(1/60)
