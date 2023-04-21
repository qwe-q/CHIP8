# Chip-8 Emulator in Python

This is a Chip-8 emulator written in Python. It can run Chip-8 ROMs and display the output on the screen.

## Getting Started
To get started with the emulator, you'll need to install Python 3 on your computer. Once you have Python installed, you can run the emulator by running the chip8.py file.

```
python3 chip8.py <path to rom>
```
The emulator will start up and run a rom. you can find a sample rom in the rom folder.

this project depends on some python libraries that you may have to install. If you can't run the app, you can try
```
pip install numpy pygame
```
## Controls
The Chip-8 has a simple 16-key keypad, which is emulated using the following keys on the keyboard:

```
1 2 3 4
Q W E R
A S D F
Z X C V
```

## Compatibility
The emulator should be compatible with most Chip-8 ROMs. However, there may be some ROMs that do not work correctly due to variations in how different emulators handle certain instructions.

## License
This project is licensed under the MIT License. Feel free to use and modify this code however you like!
