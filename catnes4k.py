#!/usr/bin/env python3
"""
nesemu 1.0 - NESEMU By A.C Holdings GUI Edition (REAL ROM LOADING + EMULATION SKELETON)
A Tkinter NES emulator frontend with partial 6502 CPU emulation,
proper ROM parsing, and a pattern‑table viewer.

This version includes:
- Centered, scalable NES display
- Correct iNES / NES 2.0 header parsing
- Trainer support
- Keyboard input (NESEMU By A.C Holdings-style mapping)
- Cycle‑aware CPU stepping
- Improved CPU core (more opcodes, fixed flags)
- Basic pattern table renderer
- FPS counter and status bar
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import time
import struct

# ----------------------------------------------------------------------
#  NES Emulator Class
# ----------------------------------------------------------------------
class NesEmuFceuxStyle:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AC NES EMU 1.X [C] Nintendo 1985-2026 [C] A.C Holdings 1999-2026 beta 0.1")
        self.root.geometry("640x480")
        self.root.resizable(True, True)
        self.root.configure(bg="#222222")

        # NES screen dimensions (256x240, scaled)
        self.scale = 2.0                     # start with 2x scaling
        self.screen_width = int(256 * self.scale)
        self.screen_height = int(240 * self.scale)

        # === NESEMU By A.C Holdings-STYLE MENU BAR ===
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open ROM...", command=self.load_rom, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Close ROM", command=self.close_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)

        # Config menu
        config_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Config", menu=config_menu)
        config_menu.add_command(label="Video...", command=self.dummy_nesemu)
        config_menu.add_command(label="Sound...", command=self.dummy_nesemu)
        config_menu.add_command(label="Input...", command=self.open_controller_config)
        config_menu.add_command(label="Palette...", command=self.dummy_nesemu)
        config_menu.add_separator()
        config_menu.add_command(label="Save Config", command=self.dummy_nesemu)

        # Controllers menu (NESEMU By A.C Holdings-style input config)
        controllers_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Controllers", menu=controllers_menu)
        controllers_menu.add_command(label="Configure Keyboard...", command=self.open_controller_config)
        controllers_menu.add_command(label="Reset To NESEMU By A.C Holdings Defaults", command=self.reset_controller_bindings)

        # Machine menu
        machine_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Machine", menu=machine_menu)
        machine_menu.add_command(label="Power On / Reset", command=self.start_emulation)
        machine_menu.add_command(label="Power Off", command=self.stop_emulation)
        machine_menu.add_separator()
        machine_menu.add_command(label="Insert Coin", command=self.dummy_nesemu)
        machine_menu.add_command(label="FDS Disk Side", command=self.dummy_nesemu)

        # Emulation menu
        emu_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Emulation", menu=emu_menu)
        emu_menu.add_command(label="Start / Resume", command=self.start_emulation)
        emu_menu.add_command(label="Pause", command=self.pause_emulation)
        emu_menu.add_command(label="Stop", command=self.stop_emulation)
        emu_menu.add_separator()
        emu_menu.add_command(label="Speed 100%", command=self.dummy_nesemu)
        emu_menu.add_command(label="Speed 200%", command=self.dummy_nesemu)

        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Cheat...", command=self.dummy_nesemu)
        tools_menu.add_command(label="Lua Script...", command=self.dummy_nesemu)
        tools_menu.add_command(label="Debug...", command=self.dummy_nesemu)

        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Controls", command=self.show_controls)
        help_menu.add_command(label="Project Roadmap...", command=self.show_roadmap)
        help_menu.add_command(label="About NESEMU By A.C Holdings / nesemu 1.0", command=self.show_about)

        # === TOOLBAR ===
        toolbar = tk.Frame(self.root, bg="#333333", height=30)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        tk.Button(toolbar, text="▶", width=3, command=self.start_emulation,
                  bg="black", fg="blue").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="⏸", width=3, command=self.pause_emulation,
                  bg="black", fg="blue").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="⏹", width=3, command=self.stop_emulation,
                  bg="black", fg="blue").pack(side=tk.LEFT, padx=2)
        tk.Label(toolbar, text="ROM:", bg="#333333", fg="white").pack(side=tk.LEFT, padx=5)
        self.rom_label = tk.Label(toolbar, text="No ROM", bg="#333333", fg="#00ff00",
                                  font=("Courier", 9))
        self.rom_label.pack(side=tk.LEFT)

        # === MAIN NES DISPLAY CANVAS ===
        self.canvas_frame = tk.Frame(self.root, bg="#000000")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=self.screen_width,
            height=self.screen_height,
            bg="#000000",
            highlightthickness=2,
            highlightbackground="#4444ff"
        )
        self.canvas.pack(expand=True, anchor=tk.CENTER)

        # Bind resize event to update canvas scaling
        self.canvas_frame.bind("<Configure>", self.on_frame_resize)

        # === STATUS BAR ===
        self.status_frame = tk.Frame(self.root, bg="#111111")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.fps_label = tk.Label(self.status_frame, text="FPS: 60.0", bg="#111111",
                                  fg="#00ff00", font=("Courier", 9))
        self.fps_label.pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(
            self.status_frame,
            text="nesemu 1.0 — Ready (NESEMU By A.C Holdings style)",
            bg="#111111",
            fg="#00ff00",
            font=("Courier", 9)
        )
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.rom_info = tk.Label(self.status_frame, text="Header: None", bg="#111111",
                                 fg="#ffff00", font=("Courier", 8))
        self.rom_info.pack(side=tk.RIGHT, padx=5)

        # Emulation state
        self.running = False
        self.paused = False
        self.rom_loaded = False
        self.current_rom_path = None
        self.rom_data = None
        self.prg_rom = b""
        self.chr_rom = b""
        self.mapper = 0
        self.mirroring = "Horizontal"
        self.tv_system = "NTSC"
        self.scanlines_per_frame = 262
        self.cpu_cycles_per_frame = 29780
        self.frame_count = 0
        self.last_time = time.time()
        self.cpu_ready = False
        self.cpu_halted = False
        self.last_opcode = 0x00
        self.unimplemented_opcode_count = 0
        self.last_unimplemented_opcode = None

        # 6502 core state
        self.mem = bytearray(65536)
        self.pc = 0x0000
        self.sp = 0xFD
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.p = 0x24          # NV‑B‑D‑IZC  (B = 1, I = 1)
        self.cycle = 0
        self.cpu_cycles_total = 0
        self.cpu_stall_cycles = 0

        # PPU core state (hardware-backed, mapper-0 oriented)
        self.ppu_ctrl = 0x00      # $2000
        self.ppu_mask = 0x00      # $2001
        self.ppu_status = 0x00    # $2002
        self.ppu_oam_addr = 0x00  # $2003
        self.ppu_scroll_x = 0x00
        self.ppu_scroll_y = 0x00
        self.ppu_addr = 0x0000
        self.ppu_addr_latch = 0
        self.ppu_data_buffer = 0x00
        self.ppu_cycle = 0
        self.ppu_scanline = 261
        self.ppu_frame = 0
        self.ppu_nmi_pending = False
        self.ppu_oam = bytearray(256)
        self.ppu_vram = bytearray(0x1000)    # 4 nametables (mirroring handled in mapper)
        self.ppu_palette_ram = bytearray(32)
        self.chr_ram = None
        self.cpu_odd_cycle = False
        self.mapper_prg_bank = 0
        self.mapper_chr_bank = 0

        # Keyboard controller mapping (NESEMU By A.C Holdings-style defaults)
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)
        self.controller_bindings_default = {
            "Right": "Right",
            "Left": "Left",
            "Down": "Down",
            "Up": "Up",
            "A": "z",
            "B": "x",
            "Start": "Return",
            "Select": "BackSpace",
        }
        self.controller_bindings = dict(self.controller_bindings_default)
        self.action_state = {action: False for action in self.controller_bindings}
        # Controller state for $4016/$4017 (strobe)
        self.controller_state = [0, 0]   # player 0 and 1
        self.controller_strobe = False
        self.controller_shift = [0, 0]
        self.controller_index = [0, 0]

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Precompute some color tables
        self.palette = self.build_palette()

        print("nesemu 1.0 (NESEMU By A.C Holdings GUI) started!")
        print("REAL ROM loading + header parsing active")
        print("Keyboard mapping: Arrow keys = D-pad, Z = A, X = B, Enter = Start, Backspace = Select")
        print("→ Drop your Cython 6502/PPU core into run_frame_loop for full speed emulation")

    # ------------------------------------------------------------------
    #  ROM Loading
    # ------------------------------------------------------------------
    def detect_tv_system(self, is_nes2, flags9, flags10, filename):
        """Best-effort TV system detection from headers/filename."""
        if is_nes2:
            mode = (flags10 >> 2) & 0x03
            if mode == 1:
                return "PAL"
            if mode == 2:
                return "Dendy"
            if mode == 3:
                return "Multi"
            return "NTSC"
        # iNES bit0 of flags9: 0 NTSC, 1 PAL
        if flags9 & 0x01:
            return "PAL"
        upper = filename.upper()
        if "(E)" in upper or "PAL" in upper:
            return "PAL"
        if "DENDY" in upper:
            return "Dendy"
        return "NTSC"

    def configure_timing_for_tv_system(self):
        if self.tv_system == "PAL":
            self.scanlines_per_frame = 312
            self.cpu_cycles_per_frame = 33247
        elif self.tv_system == "Dendy":
            self.scanlines_per_frame = 312
            self.cpu_cycles_per_frame = 35469
        else:
            self.scanlines_per_frame = 262
            self.cpu_cycles_per_frame = 29780

    def mapper_supported(self, mapper):
        return mapper in (0, 2, 3, 7)

    def load_rom(self):
        file_path = filedialog.askopenfilename(
            title="Open NES ROM (NESEMU By A.C Holdings style)",
            filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                self.rom_data = f.read()

            # Validate iNES header
            if len(self.rom_data) < 16 or self.rom_data[:4] != b'NES\x1a':
                raise ValueError("Not a valid iNES ROM")

            # Parse header
            prg_banks = self.rom_data[4]
            chr_banks = self.rom_data[5]
            flags6 = self.rom_data[6]
            flags7 = self.rom_data[7]
            flags8 = self.rom_data[8] if len(self.rom_data) > 8 else 0
            flags9 = self.rom_data[9] if len(self.rom_data) > 9 else 0
            flags10 = self.rom_data[10] if len(self.rom_data) > 10 else 0
            flags11 = self.rom_data[11] if len(self.rom_data) > 11 else 0
            flags12 = self.rom_data[12] if len(self.rom_data) > 12 else 0
            flags13 = self.rom_data[13] if len(self.rom_data) > 13 else 0
            flags14 = self.rom_data[14] if len(self.rom_data) > 14 else 0
            flags15 = self.rom_data[15] if len(self.rom_data) > 15 else 0

            # Detect NES 2.0
            is_nes2 = ((flags7 & 0x0C) == 0x08) and (flags8 & 0x0F) == 0x0F

            # Trainer presence
            trainer = 512 if (flags6 & 0x04) else 0

            # Mapper
            if is_nes2:
                mapper = (flags6 >> 4) | (flags7 & 0xF0) | ((flags8 & 0x0F) << 8)
            else:
                # Old iNES: only 4 bits from flags6, and up to 4 bits from flags7
                mapper = ((flags6 >> 4) & 0x0F) | (flags7 & 0xF0)

            # Mirroring
            mirror = "Vertical" if (flags6 & 1) else "Horizontal"
            if flags6 & 0x08:
                # Four-screen mirroring overrides
                mirror = "Four-Screen"
                # If four-screen, the flag bit is set and there is additional VRAM
                # We ignore for simplicity.

            # PRG size
            if is_nes2:
                prg_size = (prg_banks | ((flags9 & 0x0F) << 8)) * 16384
                chr_size = (chr_banks | ((flags9 & 0xF0) << 4)) * 8192
            else:
                prg_size = prg_banks * 16384
                chr_size = chr_banks * 8192

            if prg_size == 0:
                raise ValueError("ROM has no PRG data")

            # Extract ROM data
            prg_start = 16 + trainer
            prg_end = prg_start + prg_size
            chr_end = prg_end + chr_size

            if prg_end > len(self.rom_data):
                raise ValueError("ROM PRG section is truncated")

            self.prg_rom = self.rom_data[prg_start:prg_end]
            self.chr_rom = self.rom_data[prg_end:chr_end] if chr_end <= len(self.rom_data) else b""
            self.mapper = mapper
            self.mirroring = mirror
            self.tv_system = self.detect_tv_system(is_nes2, flags9, flags10, file_path.split("/")[-1])
            self.configure_timing_for_tv_system()

            self.current_rom_path = file_path
            self.rom_loaded = True

            self.rom_label.config(text=file_path.split("/")[-1])
            header_type = "NES2.0" if is_nes2 else "iNES"
            self.rom_info.config(
                text=f"{header_type} PRG:{prg_size//1024}K CHR:{chr_size//1024}K Mapper:{mapper} Mirror:{mirror} TV:{self.tv_system}"
            )
            self.status.config(text=f"nesemu 1.0 — ROM loaded: {file_path.split('/')[-1]} | Ready for real emulation")

            mapper_note = "Mapper supported." if self.mapper_supported(mapper) else "Mapper not implemented yet; ROM may not boot."
            messagebox.showinfo(
                "nesemu 1.0",
                f"✅ REAL ROM loaded!\n\nHeader parsed successfully.\nPRG: {prg_size//1024}KB | CHR: {chr_size//1024}KB\nMapper: {mapper}\nTV: {self.tv_system}\n\n{mapper_note}"
            )
        except Exception as e:
            messagebox.showerror("nesemu 1.0", f"Failed to load ROM:\n{str(e)}")

    def close_rom(self):
        if self.rom_loaded:
            self.stop_emulation()
            self.rom_loaded = False
            self.current_rom_path = None
            self.rom_data = None
            self.prg_rom = b""
            self.chr_rom = b""
            self.mapper = 0
            self.tv_system = "NTSC"
            self.configure_timing_for_tv_system()
            self.cpu_ready = False
            self.cpu_halted = False
            self.unimplemented_opcode_count = 0
            self.last_unimplemented_opcode = None
            self.rom_label.config(text="No ROM")
            self.rom_info.config(text="Header: None")
            self.status.config(text="nesemu 1.0 — ROM closed")

    # ------------------------------------------------------------------
    #  NROM (Mapper 0) Boot
    # ------------------------------------------------------------------
    def boot_nrom(self):
        """Initialize cartridge/CPU/PPU state and jump to reset vector."""
        self.mem = bytearray(65536)
        self.cpu_halted = False
        self.unimplemented_opcode_count = 0
        self.last_unimplemented_opcode = None
        self.cpu_cycles_total = 0
        self.cpu_stall_cycles = 0
        self.cpu_odd_cycle = False

        # Reset PPU registers/state
        self.ppu_ctrl = 0x00
        self.ppu_mask = 0x00
        self.ppu_status = 0x00
        self.ppu_oam_addr = 0x00
        self.ppu_scroll_x = 0x00
        self.ppu_scroll_y = 0x00
        self.ppu_addr = 0x0000
        self.ppu_addr_latch = 0
        self.ppu_data_buffer = 0x00
        self.ppu_cycle = 0
        self.ppu_scanline = 261
        self.ppu_frame = 0
        self.ppu_nmi_pending = False
        self.ppu_oam = bytearray(256)
        self.ppu_vram = bytearray(0x1000)
        self.ppu_palette_ram = bytearray(32)
        # CHR-RAM cartridge if no CHR-ROM is provided
        self.chr_ram = bytearray(0x2000) if len(self.chr_rom) == 0 else None
        self.mapper_prg_bank = 0
        self.mapper_chr_bank = 0

        # Mapper 7 forces single-screen mirroring selected by register bit 4.
        if self.mapper == 7:
            self.mirroring = "Single-Screen Lower"

        prg_len = len(self.prg_rom)
        if self.mapper == 0:
            if prg_len == 16384:
                # NROM-128: mirror 16KB into both banks
                self.mem[0x8000:0xC000] = self.prg_rom
                self.mem[0xC000:0x10000] = self.prg_rom
            elif prg_len == 32768:
                # NROM-256
                self.mem[0x8000:0x10000] = self.prg_rom
            else:
                raise ValueError(f"Unsupported PRG size for NROM: {prg_len} bytes")
        elif prg_len < 16384:
            raise ValueError(f"PRG too small for mapper {self.mapper}: {prg_len} bytes")

        # Initialize CPU registers
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.sp = 0xFD
        self.p = 0x24
        self.pc = self.read16(0xFFFC)
        if self.pc == 0x0000 or self.pc == 0xFFFF:
            raise ValueError(f"Invalid reset vector ${self.pc:04X}")
        self.cpu_ready = True

    # ------------------------------------------------------------------
    #  Emulation Control
    # ------------------------------------------------------------------
    def start_emulation(self):
        if not self.rom_loaded:
            messagebox.showwarning("nesemu 1.0", "Load a .nes ROM first! (NESEMU By A.C Holdings style)")
            return
        if not self.mapper_supported(self.mapper):
            messagebox.showwarning(
                "nesemu 1.0",
                f"Mapper {self.mapper} is not implemented yet.\nSupported now: 0 (NROM), 2 (UxROM), 3 (CNROM), 7 (AxROM)."
            )
            return
        try:
            self.boot_nrom()
        except Exception as e:
            messagebox.showerror("nesemu 1.0", f"Boot failed:\n{e}")
            return
        self.running = True
        self.paused = False
        self.status.config(text=f"nesemu 1.0 — BOOTED | PC=${self.pc:04X}")
        self.run_frame_loop()

    def pause_emulation(self):
        self.paused = True
        self.status.config(text="nesemu 1.0 — PAUSED")

    def stop_emulation(self):
        self.running = False
        self.paused = False
        self.cpu_ready = False
        self.cpu_halted = False
        self.status.config(text="nesemu 1.0 — Stopped")

    # ------------------------------------------------------------------
    #  Memory Access (CPU)
    # ------------------------------------------------------------------
    def mapper_cpu_read(self, addr):
        if not self.prg_rom:
            return 0xFF
        a = addr & 0xFFFF
        prg_len = len(self.prg_rom)
        prg_banks_16k = max(1, prg_len // 0x4000)

        if self.mapper == 0:
            if prg_len == 0x4000:
                return self.prg_rom[(a - 0x8000) & 0x3FFF]
            return self.prg_rom[(a - 0x8000) % prg_len]

        if self.mapper == 2:
            # UxROM: $8000-$BFFF switchable, $C000-$FFFF fixed last bank.
            if a < 0xC000:
                bank = self.mapper_prg_bank % prg_banks_16k
                return self.prg_rom[bank * 0x4000 + (a - 0x8000)]
            bank = prg_banks_16k - 1
            return self.prg_rom[bank * 0x4000 + (a - 0xC000)]

        if self.mapper == 3:
            # CNROM: fixed PRG, switchable CHR only.
            if prg_len == 0x4000:
                return self.prg_rom[(a - 0x8000) & 0x3FFF]
            return self.prg_rom[(a - 0x8000) % prg_len]

        if self.mapper == 7:
            # AxROM: 32KB switchable PRG banks.
            prg_banks_32k = max(1, prg_len // 0x8000)
            bank = self.mapper_prg_bank % prg_banks_32k
            return self.prg_rom[bank * 0x8000 + (a - 0x8000)]

        # Fallback: linear map to reduce hard failures.
        return self.prg_rom[(a - 0x8000) % prg_len]

    def mapper_cpu_write(self, addr, value):
        value &= 0xFF
        if self.mapper == 2:
            self.mapper_prg_bank = value & 0x0F
        elif self.mapper == 3:
            self.mapper_chr_bank = value & 0x03
        elif self.mapper == 7:
            self.mapper_prg_bank = value & 0x07
            self.mirroring = "Single-Screen Upper" if (value & 0x10) else "Single-Screen Lower"

    def mapper_ppu_read_chr(self, ppu_addr):
        if self.chr_ram is not None:
            return self.chr_ram[ppu_addr & 0x1FFF]
        if not self.chr_rom:
            return 0x00
        if self.mapper == 3 and len(self.chr_rom) >= 0x2000:
            banks = max(1, len(self.chr_rom) // 0x2000)
            bank = self.mapper_chr_bank % banks
            return self.chr_rom[bank * 0x2000 + (ppu_addr & 0x1FFF)]
        return self.chr_rom[ppu_addr % len(self.chr_rom)]

    def mapper_ppu_write_chr(self, ppu_addr, value):
        if self.chr_ram is not None:
            self.chr_ram[ppu_addr & 0x1FFF] = value & 0xFF

    def read8(self, addr):
        addr &= 0xFFFF
        # CPU RAM mirrors every 0x800 up to 0x1FFF
        if addr < 0x2000:
            return self.mem[addr & 0x07FF]
        # PPU registers mirrored every 8 bytes
        if 0x2000 <= addr <= 0x3FFF:
            return self.read_ppu_register(0x2000 + (addr & 0x7))
        # For simplicity, ignore other registers except controller
        if addr == 0x4016:
            return self.read_controller(0)
        if addr == 0x4017:
            return self.read_controller(1)
        # Ignore writes to PRG ROM (above 0x8000)
        if addr >= 0x8000:
            return self.mapper_cpu_read(addr)
        return self.mem[addr]

    def write8(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if addr < 0x2000:
            self.mem[addr & 0x07FF] = value
        elif 0x2000 <= addr <= 0x3FFF:
            self.write_ppu_register(0x2000 + (addr & 0x7), value)
        elif addr == 0x4014:
            # OAM DMA: copy 256 bytes from CPU page into PPU OAM.
            page = (value & 0xFF) << 8
            for i in range(256):
                self.ppu_oam[(self.ppu_oam_addr + i) & 0xFF] = self.read8(page + i)
            # CPU is stalled for 513 or 514 cycles depending on parity.
            self.cpu_stall_cycles += 513 + (1 if self.cpu_odd_cycle else 0)
        elif addr == 0x4016:
            # Controller strobe
            prev = self.controller_strobe
            self.controller_strobe = (value & 1) != 0
            if self.controller_strobe:
                self.latch_controllers()
            elif prev and not self.controller_strobe:
                # Common software latches on 1->0 transition.
                self.latch_controllers()
        else:
            # Other writes (PPU, APU) ignored for now
            if addr >= 0x8000:
                self.mapper_cpu_write(addr, value)
                return
            self.mem[addr] = value

    def ppu_mirror_nametable_addr(self, ppu_addr):
        """Map $2000-$2FFF into CIRAM based on mapper-0 mirroring."""
        offset = (ppu_addr - 0x2000) & 0x0FFF
        table = (offset >> 10) & 0x03
        inner = offset & 0x03FF
        if self.mirroring == "Vertical":
            # NT0,NT1,NT0,NT1
            mapped = table & 0x01
        elif self.mirroring == "Four-Screen":
            mapped = table
        elif self.mirroring == "Single-Screen Upper":
            mapped = 1
        elif self.mirroring == "Single-Screen Lower":
            mapped = 0
        else:
            # Horizontal: NT0,NT0,NT1,NT1
            mapped = (table >> 1) & 0x01
        return (mapped * 0x0400 + inner) & 0x0FFF

    def ppu_palette_addr(self, ppu_addr):
        addr = (ppu_addr - 0x3F00) & 0x1F
        # Palette mirrors (universal background mirrors)
        if addr in (0x10, 0x14, 0x18, 0x1C):
            addr -= 0x10
        return addr

    def ppu_read(self, ppu_addr):
        ppu_addr &= 0x3FFF
        if ppu_addr < 0x2000:
            return self.mapper_ppu_read_chr(ppu_addr)
        if ppu_addr < 0x3F00:
            return self.ppu_vram[self.ppu_mirror_nametable_addr(ppu_addr)]
        return self.ppu_palette_ram[self.ppu_palette_addr(ppu_addr)]

    def ppu_write(self, ppu_addr, value):
        ppu_addr &= 0x3FFF
        value &= 0xFF
        if ppu_addr < 0x2000:
            self.mapper_ppu_write_chr(ppu_addr, value)
            return
        if ppu_addr < 0x3F00:
            self.ppu_vram[self.ppu_mirror_nametable_addr(ppu_addr)] = value
            return
        self.ppu_palette_ram[self.ppu_palette_addr(ppu_addr)] = value

    def read_ppu_register(self, reg):
        if reg == 0x2002:  # PPUSTATUS
            value = self.ppu_status
            self.ppu_status &= ~0x80  # clear vblank
            self.ppu_nmi_pending = False
            self.ppu_addr_latch = 0
            return value
        if reg == 0x2004:  # OAMDATA
            return self.ppu_oam[self.ppu_oam_addr]
        if reg == 0x2007:  # PPUDATA (buffered reads)
            value = self.ppu_read(self.ppu_addr)
            if self.ppu_addr < 0x3F00:
                result = self.ppu_data_buffer
                self.ppu_data_buffer = value
            else:
                result = value
                self.ppu_data_buffer = self.ppu_read((self.ppu_addr - 0x1000) & 0x3FFF)
            inc = 32 if (self.ppu_ctrl & 0x04) else 1
            self.ppu_addr = (self.ppu_addr + inc) & 0x3FFF
            return result
        return 0x00

    def write_ppu_register(self, reg, value):
        value &= 0xFF
        if reg == 0x2000:  # PPUCTRL
            prev = self.ppu_ctrl
            self.ppu_ctrl = value
            # If NMI is enabled while already in vblank, trigger NMI edge.
            if (self.ppu_status & 0x80) and not (prev & 0x80) and (value & 0x80):
                self.ppu_nmi_pending = True
            return
        if reg == 0x2001:  # PPUMASK
            self.ppu_mask = value
            return
        if reg == 0x2003:  # OAMADDR
            self.ppu_oam_addr = value
            return
        if reg == 0x2004:  # OAMDATA
            self.ppu_oam[self.ppu_oam_addr] = value
            self.ppu_oam_addr = (self.ppu_oam_addr + 1) & 0xFF
            return
        if reg == 0x2005:  # PPUSCROLL
            if self.ppu_addr_latch == 0:
                self.ppu_scroll_x = value
                self.ppu_addr_latch = 1
            else:
                self.ppu_scroll_y = value
                self.ppu_addr_latch = 0
            return
        if reg == 0x2006:  # PPUADDR
            if self.ppu_addr_latch == 0:
                self.ppu_addr = ((value & 0x3F) << 8) | (self.ppu_addr & 0x00FF)
                self.ppu_addr_latch = 1
            else:
                self.ppu_addr = (self.ppu_addr & 0xFF00) | value
                self.ppu_addr_latch = 0
            return
        if reg == 0x2007:  # PPUDATA
            self.ppu_write(self.ppu_addr, value)
            inc = 32 if (self.ppu_ctrl & 0x04) else 1
            self.ppu_addr = (self.ppu_addr + inc) & 0x3FFF

    def service_nmi(self):
        self.push8((self.pc >> 8) & 0xFF)
        self.push8(self.pc & 0xFF)
        self.push8((self.p & ~0x10) | 0x20)
        self.set_flag(0x04, True)
        vector = self.read16(0xFFFA)
        if vector not in (0x0000, 0xFFFF):
            self.pc = vector
        self.ppu_nmi_pending = False

    def ppu_step(self):
        """Advance PPU by one dot and maintain vblank/NMI timing."""
        self.ppu_cycle += 1
        if self.ppu_cycle >= 341:
            self.ppu_cycle = 0
            self.ppu_scanline += 1
            if self.ppu_scanline >= self.scanlines_per_frame:
                self.ppu_scanline = 0
                self.ppu_frame += 1

        # Enter vblank: scanline 241, dot 1
        if self.ppu_scanline == 241 and self.ppu_cycle == 1:
            self.ppu_status |= 0x80
            if self.ppu_ctrl & 0x80:
                self.ppu_nmi_pending = True

        # Pre-render line clears vblank/sprite flags
        pre_render = self.scanlines_per_frame - 1
        if self.ppu_scanline == pre_render and self.ppu_cycle == 1:
            self.ppu_status &= ~0xE0

    def read16(self, addr):
        lo = self.read8(addr)
        hi = self.read8((addr + 1) & 0xFFFF)
        return lo | (hi << 8)

    def read16_zp(self, addr8):
        """Zero-page 16-bit read with wraparound (for indexed indirect modes)."""
        a = addr8 & 0xFF
        lo = self.read8(a)
        hi = self.read8((a + 1) & 0xFF)
        return lo | (hi << 8)

    def page_crossed(self, base, addr):
        return (base & 0xFF00) != (addr & 0xFF00)

    # ------------------------------------------------------------------
    #  Keyboard -> Controller
    # ------------------------------------------------------------------
    def update_controller_state(self):
        # Update state from keys
        # Player 0 (standard NES controller)
        self.controller_state[0] = 0
        if self.action_state["Right"]:   self.controller_state[0] |= 0x01
        if self.action_state["Left"]:    self.controller_state[0] |= 0x02
        if self.action_state["Down"]:    self.controller_state[0] |= 0x04
        if self.action_state["Up"]:      self.controller_state[0] |= 0x08
        if self.action_state["A"]:       self.controller_state[0] |= 0x10
        if self.action_state["B"]:       self.controller_state[0] |= 0x20
        if self.action_state["Start"]:   self.controller_state[0] |= 0x40
        if self.action_state["Select"]:  self.controller_state[0] |= 0x80
        # Player 1 keyboard mapping is not configured yet.
        self.controller_state[1] = 0

    def latch_controllers(self):
        """Latch controller states into shift registers for serial reads."""
        self.update_controller_state()
        self.controller_shift[0] = self.controller_state[0] & 0xFF
        self.controller_shift[1] = self.controller_state[1] & 0xFF
        self.controller_index[0] = 0
        self.controller_index[1] = 0

    def normalize_key_name(self, key_name):
        if not key_name:
            return ""
        return key_name.lower() if len(key_name) == 1 else key_name

    def get_action_for_key(self, keysym):
        norm = self.normalize_key_name(keysym)
        for action, bound_key in self.controller_bindings.items():
            if self.normalize_key_name(bound_key) == norm:
                return action
        return None

    def open_controller_config(self):
        win = tk.Toplevel(self.root)
        win.title("Controller Config (Keyboard)")
        win.geometry("360x320")
        win.resizable(False, False)
        win.configure(bg="#222222")
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win,
            text="NESEMU By A.C Holdings-style keyboard mapping\n(Enter Tk keysym names)",
            bg="#222222",
            fg="#00ff88",
            font=("Courier", 10)
        ).pack(pady=8)

        form = tk.Frame(win, bg="#222222")
        form.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        entries = {}
        for idx, action in enumerate(("Up", "Down", "Left", "Right", "A", "B", "Start", "Select")):
            tk.Label(form, text=action, bg="#222222", fg="white", anchor="w", width=10).grid(row=idx, column=0, sticky="w", pady=3)
            ent = tk.Entry(form, width=18, bg="#111111", fg="#00ff00", insertbackground="#00ff00")
            ent.grid(row=idx, column=1, sticky="w", pady=3)
            ent.insert(0, self.controller_bindings[action])
            entries[action] = ent

        def save_bindings():
            new_map = {}
            seen = set()
            for action, ent in entries.items():
                key = ent.get().strip()
                if not key:
                    messagebox.showwarning("Controllers", f"{action} cannot be empty.", parent=win)
                    return
                norm = self.normalize_key_name(key)
                if norm in seen:
                    messagebox.showwarning("Controllers", f"Duplicate key '{key}' is not allowed.", parent=win)
                    return
                seen.add(norm)
                new_map[action] = key
            self.controller_bindings = new_map
            self.action_state = {action: False for action in self.controller_bindings}
            self.update_controller_state()
            self.latch_controllers()
            self.status.config(text="nesemu 1.0 — Controller keyboard mapping updated")
            win.destroy()

        btns = tk.Frame(win, bg="#222222")
        btns.pack(pady=8)
        tk.Button(btns, text="Save", command=save_bindings, bg="black", fg="blue", width=10).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Cancel", command=win.destroy, bg="black", fg="blue", width=10).pack(side=tk.LEFT, padx=4)

    def reset_controller_bindings(self):
        self.controller_bindings = dict(self.controller_bindings_default)
        self.action_state = {action: False for action in self.controller_bindings}
        self.update_controller_state()
        self.latch_controllers()
        messagebox.showinfo(
            "Controllers",
            "Controller mapping reset to NESEMU By A.C Holdings-style defaults:\n"
            "Arrows = D-pad, Z = A, X = B, Enter = Start, BackSpace = Select"
        )

    def show_controls(self):
        messagebox.showinfo(
            "Controls",
            "Keyboard controls (Player 1):\n\n"
            "Arrow keys = D-pad\n"
            "Z = A\n"
            "X = B\n"
            "Enter = Start\n"
            "BackSpace = Select\n\n"
            "Use Controllers -> Configure Keyboard... to change keys."
        )

    def read_controller(self, player):
        player &= 1
        if self.controller_strobe:
            # While strobe is high, always return current A button state.
            self.update_controller_state()
            return self.controller_state[player] & 0x01

        if self.controller_index[player] < 8:
            bit = (self.controller_shift[player] >> self.controller_index[player]) & 0x01
        else:
            # Standard NES controllers keep returning 1 after 8 shifts.
            bit = 1
        self.controller_index[player] += 1
        return bit

    # ------------------------------------------------------------------
    #  CPU Flags
    # ------------------------------------------------------------------
    def set_flag(self, bit, enabled):
        if enabled:
            self.p |= bit
        else:
            self.p &= ~bit

    def get_flag(self, bit):
        return 1 if (self.p & bit) else 0

    def set_zn(self, value):
        value &= 0xFF
        # Z flag
        self.set_flag(0x02, value == 0)
        # N flag
        self.set_flag(0x80, (value & 0x80) != 0)

    # ------------------------------------------------------------------
    #  Stack Operations
    # ------------------------------------------------------------------
    def push8(self, value):
        self.mem[0x0100 + self.sp] = value & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def pop8(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.mem[0x0100 + self.sp]

    # ------------------------------------------------------------------
    #  Arithmetic (ADC/SBC)
    # ------------------------------------------------------------------
    def adc(self, value):
        value &= 0xFF
        carry = self.get_flag(0x01)
        result = self.a + value + carry
        res8 = result & 0xFF
        # Carry
        self.set_flag(0x01, result > 0xFF)
        # Overflow
        overflow = ((~(self.a ^ value) & (self.a ^ res8)) & 0x80) != 0
        self.set_flag(0x40, overflow)
        self.a = res8
        self.set_zn(self.a)

    def sbc(self, value):
        # 6502 SBC == ADC with one's complement
        self.adc(value ^ 0xFF)

    # ------------------------------------------------------------------
    #  Branching
    # ------------------------------------------------------------------
    def branch(self, take):
        offset = self.read8(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        extra = 0
        if take:
            old_pc = self.pc
            if offset & 0x80:
                offset -= 0x100
            self.pc = (self.pc + offset) & 0xFFFF
            # Branch taken: +1 cycle, and +1 if page boundary crossed.
            extra = 1
            if (old_pc & 0xFF00) != (self.pc & 0xFF00):
                extra += 1
        return extra

    def get_opcode_cycles(self, op):
        """Approximate 6502 base cycles for implemented opcodes."""
        table = {
            # NOP + unofficial immediate NOPs
            0xEA: 2, 0x1A: 2, 0x3A: 2, 0x5A: 2, 0x7A: 2, 0xDA: 2, 0xFA: 2,
            0x80: 2, 0x82: 2, 0x89: 2, 0xC2: 2, 0xE2: 2,
            # Flags
            0x78: 2, 0x58: 2, 0xD8: 2, 0x18: 2, 0x38: 2, 0xB8: 2,
            # LDA
            0xA9: 2, 0xA5: 3, 0xB5: 4, 0xAD: 4, 0xBD: 4, 0xB9: 4, 0xA1: 6, 0xB1: 5,
            # LDX
            0xA2: 2, 0xA6: 3, 0xB6: 4, 0xAE: 4, 0xBE: 4,
            # LDY
            0xA0: 2, 0xA4: 3, 0xB4: 4, 0xAC: 4, 0xBC: 4,
            # STA/STX/STY
            0x8D: 4, 0x85: 3, 0x95: 4, 0x9D: 5, 0x99: 5, 0x81: 6, 0x91: 6,
            0x8E: 4, 0x86: 3, 0x96: 4, 0x8C: 4, 0x84: 3, 0x94: 4,
            # Transfers
            0xAA: 2, 0xA8: 2, 0x8A: 2, 0x98: 2, 0xBA: 2, 0x9A: 2,
            # INC/DEC register
            0xE8: 2, 0xC8: 2, 0xCA: 2, 0x88: 2,
            # INC/DEC memory
            0xE6: 5, 0xF6: 6, 0xEE: 6, 0xFE: 7, 0xC6: 5, 0xD6: 6, 0xCE: 6, 0xDE: 7,
            # BIT
            0x24: 3, 0x2C: 4,
            # AND
            0x29: 2, 0x25: 3, 0x35: 4, 0x2D: 4, 0x3D: 4, 0x39: 4, 0x21: 6, 0x31: 5,
            # ORA
            0x09: 2, 0x05: 3, 0x15: 4, 0x0D: 4, 0x1D: 4, 0x19: 4, 0x01: 6, 0x11: 5,
            # EOR
            0x49: 2, 0x45: 3, 0x55: 4, 0x4D: 4, 0x5D: 4, 0x59: 4, 0x41: 6, 0x51: 5,
            # ADC
            0x69: 2, 0x65: 3, 0x75: 4, 0x6D: 4, 0x7D: 4, 0x79: 4, 0x61: 6, 0x71: 5,
            # SBC
            0xE9: 2, 0xE5: 3, 0xF5: 4, 0xED: 4, 0xFD: 4, 0xF9: 4, 0xE1: 6, 0xF1: 5,
            # CMP
            0xC9: 2, 0xC5: 3, 0xD5: 4, 0xCD: 4, 0xDD: 4, 0xD9: 4, 0xC1: 6, 0xD1: 5,
            # CPX/CPY
            0xE0: 2, 0xE4: 3, 0xEC: 4, 0xC0: 2, 0xC4: 3, 0xCC: 4,
            # Stack
            0x48: 3, 0x68: 4, 0x08: 3, 0x28: 4,
            # Shifts/rotates A
            0x0A: 2, 0x4A: 2, 0x2A: 2, 0x6A: 2,
            # Shifts/rotates memory
            0x06: 5, 0x16: 6, 0x0E: 6, 0x1E: 7,
            0x46: 5, 0x56: 6, 0x4E: 6, 0x5E: 7,
            0x26: 5, 0x36: 6, 0x2E: 6, 0x3E: 7,
            0x66: 5, 0x76: 6, 0x6E: 6, 0x7E: 7,
            # Jumps/calls
            0x4C: 3, 0x6C: 5, 0x20: 6, 0x60: 6, 0x40: 6,
            # Branches (base only, branch() adds extras)
            0xF0: 2, 0xD0: 2, 0x10: 2, 0x30: 2, 0x90: 2, 0xB0: 2, 0x50: 2, 0x70: 2,
            # BRK
            0x00: 7,
        }
        return table.get(op, 2)

    # ------------------------------------------------------------------
    #  Rotates / Shifts (memory)
    # ------------------------------------------------------------------
    def asl_mem(self, addr):
        v = self.read8(addr)
        self.set_flag(0x01, (v & 0x80) != 0)
        v = (v << 1) & 0xFF
        self.write8(addr, v)
        self.set_zn(v)

    def lsr_mem(self, addr):
        v = self.read8(addr)
        self.set_flag(0x01, (v & 0x01) != 0)
        v = (v >> 1) & 0xFF
        self.write8(addr, v)
        self.set_zn(v)

    def rol_mem(self, addr):
        v = self.read8(addr)
        c = self.get_flag(0x01)
        self.set_flag(0x01, (v & 0x80) != 0)
        v = ((v << 1) & 0xFF) | c
        self.write8(addr, v)
        self.set_zn(v)

    def ror_mem(self, addr):
        v = self.read8(addr)
        c = self.get_flag(0x01)
        self.set_flag(0x01, (v & 0x01) != 0)
        v = ((v >> 1) & 0x7F) | (c << 7)
        self.write8(addr, v)
        self.set_zn(v)

    # ------------------------------------------------------------------
    #  CPU Step
    # ------------------------------------------------------------------
    def cpu_step(self):
        """6502 execution subset for NROM boot and early gameplay loops."""
        if not self.cpu_ready or self.cpu_halted:
            return 0

        if self.cpu_stall_cycles > 0:
            self.cpu_stall_cycles -= 1
            return 1

        if self.ppu_nmi_pending:
            self.service_nmi()
            return 7

        # Update controller state before each instruction (simulate polling)
        self.update_controller_state()

        op = self.read8(self.pc)
        self.last_opcode = op
        cycles = self.get_opcode_cycles(op)
        self.pc = (self.pc + 1) & 0xFFFF

        # ------------------------------------------------------------------
        #  Opcode handlers (grouped by category)
        # ------------------------------------------------------------------

        # ---- NOP / unofficial NOPs ----
        if op == 0xEA:               # NOP
            return 2
        if op in (0x1A, 0x3A, 0x5A, 0x7A, 0xDA, 0xFA,   # unofficial NOPs
                  0x80, 0x82, 0x89, 0xC2, 0xE2):
            # These are 2-byte NOPs (immediate) – skip operand
            self.pc = (self.pc + 1) & 0xFFFF
            return 2

        # ---- Flag instructions ----
        if op == 0x78:               # SEI
            self.set_flag(0x04, True)
            return 2
        if op == 0x58:               # CLI
            self.set_flag(0x04, False)
            return 2
        if op == 0xD8:               # CLD
            self.set_flag(0x08, False)
            return 2
        if op == 0x18:               # CLC
            self.set_flag(0x01, False)
            return 2
        if op == 0x38:               # SEC
            self.set_flag(0x01, True)
            return 2
        if op == 0xB8:               # CLV
            self.set_flag(0x40, False)
            return 2

        # ---- LDA ----
        if op == 0xA9:               # LDA #imm
            self.a = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_zn(self.a)
            return
        if op == 0xA5:               # LDA zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.a = self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0xB5:               # LDA zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a = self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0xAD:               # LDA abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.a = self.read8(addr)
            self.set_zn(self.a)
            return
        if op == 0xBD:               # LDA abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a = self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0xB9:               # LDA abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a = self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0xA1:               # LDA (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a = self.read8(self.read16_zp(ptr))
            self.set_zn(self.a)
            return
        if op == 0xB1:               # LDA (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            self.a = self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- LDX ----
        if op == 0xA2:               # LDX #imm
            self.x = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_zn(self.x)
            return
        if op == 0xA6:               # LDX zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.x = self.read8(zp)
            self.set_zn(self.x)
            return
        if op == 0xB6:               # LDX zp,Y
            zp = (self.read8(self.pc) + self.y) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.x = self.read8(zp)
            self.set_zn(self.x)
            return
        if op == 0xAE:               # LDX abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.x = self.read8(addr)
            self.set_zn(self.x)
            return
        if op == 0xBE:               # LDX abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.x = self.read8(addr)
            self.set_zn(self.x)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- LDY ----
        if op == 0xA0:               # LDY #imm
            self.y = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_zn(self.y)
            return
        if op == 0xA4:               # LDY zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.y = self.read8(zp)
            self.set_zn(self.y)
            return
        if op == 0xB4:               # LDY zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.y = self.read8(zp)
            self.set_zn(self.y)
            return
        if op == 0xAC:               # LDY abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.y = self.read8(addr)
            self.set_zn(self.y)
            return
        if op == 0xBC:               # LDY abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.y = self.read8(addr)
            self.set_zn(self.y)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- STA ----
        if op == 0x8D:               # STA abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.write8(addr, self.a)
            return
        if op == 0x85:               # STA zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(zp, self.a)
            return
        if op == 0x95:               # STA zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(zp, self.a)
            return
        if op == 0x9D:               # STA abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.write8(addr, self.a)
            return
        if op == 0x99:               # STA abs,Y
            addr = (self.read16(self.pc) + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.write8(addr, self.a)
            return
        if op == 0x81:               # STA (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(self.read16_zp(ptr), self.a)
            return
        if op == 0x91:               # STA (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8((self.read16_zp(ptr) + self.y) & 0xFFFF, self.a)
            return

        # ---- STX ----
        if op == 0x8E:               # STX abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.write8(addr, self.x)
            return
        if op == 0x86:               # STX zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(zp, self.x)
            return
        if op == 0x96:               # STX zp,Y
            zp = (self.read8(self.pc) + self.y) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(zp, self.x)
            return

        # ---- STY ----
        if op == 0x8C:               # STY abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.write8(addr, self.y)
            return
        if op == 0x84:               # STY zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(zp, self.y)
            return
        if op == 0x94:               # STY zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.write8(zp, self.y)
            return

        # ---- Transfer instructions ----
        if op == 0xAA:               # TAX
            self.x = self.a
            self.set_zn(self.x)
            return
        if op == 0xA8:               # TAY
            self.y = self.a
            self.set_zn(self.y)
            return
        if op == 0x8A:               # TXA
            self.a = self.x
            self.set_zn(self.a)
            return
        if op == 0x98:               # TYA
            self.a = self.y
            self.set_zn(self.a)
            return
        if op == 0xBA:               # TSX
            self.x = self.sp
            self.set_zn(self.x)
            return
        if op == 0x9A:               # TXS
            self.sp = self.x
            return

        # ---- Increment / Decrement ----
        if op == 0xE8:               # INX
            self.x = (self.x + 1) & 0xFF
            self.set_zn(self.x)
            return
        if op == 0xC8:               # INY
            self.y = (self.y + 1) & 0xFF
            self.set_zn(self.y)
            return
        if op == 0xCA:               # DEX
            self.x = (self.x - 1) & 0xFF
            self.set_zn(self.x)
            return
        if op == 0x88:               # DEY
            self.y = (self.y - 1) & 0xFF
            self.set_zn(self.y)
            return
        if op == 0xE6:               # INC zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            v = (self.read8(zp) + 1) & 0xFF
            self.write8(zp, v)
            self.set_zn(v)
            return
        if op == 0xF6:               # INC zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            v = (self.read8(zp) + 1) & 0xFF
            self.write8(zp, v)
            self.set_zn(v)
            return
        if op == 0xEE:               # INC abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            v = (self.read8(addr) + 1) & 0xFF
            self.write8(addr, v)
            self.set_zn(v)
            return
        if op == 0xFE:               # INC abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            v = (self.read8(addr) + 1) & 0xFF
            self.write8(addr, v)
            self.set_zn(v)
            return
        if op == 0xC6:               # DEC zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            v = (self.read8(zp) - 1) & 0xFF
            self.write8(zp, v)
            self.set_zn(v)
            return
        if op == 0xD6:               # DEC zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            v = (self.read8(zp) - 1) & 0xFF
            self.write8(zp, v)
            self.set_zn(v)
            return
        if op == 0xCE:               # DEC abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            v = (self.read8(addr) - 1) & 0xFF
            self.write8(addr, v)
            self.set_zn(v)
            return
        if op == 0xDE:               # DEC abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            v = (self.read8(addr) - 1) & 0xFF
            self.write8(addr, v)
            self.set_zn(v)
            return

        # ---- BIT ----
        if op == 0x24:               # BIT zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            v = self.read8(zp)
            self.set_flag(0x02, (self.a & v) == 0)
            self.set_flag(0x40, (v & 0x40) != 0)
            self.set_flag(0x80, (v & 0x80) != 0)
            return
        if op == 0x2C:               # BIT abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            v = self.read8(addr)
            self.set_flag(0x02, (self.a & v) == 0)
            self.set_flag(0x40, (v & 0x40) != 0)
            self.set_flag(0x80, (v & 0x80) != 0)
            return

        # ---- AND ----
        if op == 0x29:               # AND #imm
            self.a &= self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_zn(self.a)
            return
        if op == 0x25:               # AND zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.a &= self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0x35:               # AND zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a &= self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0x2D:               # AND abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.a &= self.read8(addr)
            self.set_zn(self.a)
            return
        if op == 0x3D:               # AND abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a &= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x39:               # AND abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a &= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x21:               # AND (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a &= self.read8(self.read16_zp(ptr))
            self.set_zn(self.a)
            return
        if op == 0x31:               # AND (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            self.a &= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- ORA ----
        if op == 0x09:               # ORA #imm
            self.a |= self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_zn(self.a)
            return
        if op == 0x05:               # ORA zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.a |= self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0x15:               # ORA zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a |= self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0x0D:               # ORA abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.a |= self.read8(addr)
            self.set_zn(self.a)
            return
        if op == 0x1D:               # ORA abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a |= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x19:               # ORA abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a |= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x01:               # ORA (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a |= self.read8(self.read16_zp(ptr))
            self.set_zn(self.a)
            return
        if op == 0x11:               # ORA (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            self.a |= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- EOR ----
        if op == 0x49:               # EOR #imm
            self.a ^= self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_zn(self.a)
            return
        if op == 0x45:               # EOR zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.a ^= self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0x55:               # EOR zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a ^= self.read8(zp)
            self.set_zn(self.a)
            return
        if op == 0x4D:               # EOR abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.a ^= self.read8(addr)
            self.set_zn(self.a)
            return
        if op == 0x5D:               # EOR abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a ^= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x59:               # EOR abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.a ^= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x41:               # EOR (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.a ^= self.read8(self.read16_zp(ptr))
            self.set_zn(self.a)
            return
        if op == 0x51:               # EOR (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            self.a ^= self.read8(addr)
            self.set_zn(self.a)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- ADC ----
        if op == 0x69:               # ADC #imm
            self.adc(self.read8(self.pc))
            self.pc = (self.pc + 1) & 0xFFFF
            return
        if op == 0x65:               # ADC zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.adc(self.read8(zp))
            return
        if op == 0x75:               # ADC zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.adc(self.read8(zp))
            return
        if op == 0x6D:               # ADC abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.adc(self.read8(addr))
            return
        if op == 0x7D:               # ADC abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.adc(self.read8(addr))
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x79:               # ADC abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.adc(self.read8(addr))
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0x61:               # ADC (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.adc(self.read8(self.read16_zp(ptr)))
            return
        if op == 0x71:               # ADC (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            self.adc(self.read8(addr))
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- SBC ----
        if op == 0xE9:               # SBC #imm
            self.sbc(self.read8(self.pc))
            self.pc = (self.pc + 1) & 0xFFFF
            return
        if op == 0xE5:               # SBC zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.sbc(self.read8(zp))
            return
        if op == 0xF5:               # SBC zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.sbc(self.read8(zp))
            return
        if op == 0xED:               # SBC abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.sbc(self.read8(addr))
            return
        if op == 0xFD:               # SBC abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.sbc(self.read8(addr))
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0xF9:               # SBC abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.sbc(self.read8(addr))
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0xE1:               # SBC (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.sbc(self.read8(self.read16_zp(ptr)))
            return
        if op == 0xF1:               # SBC (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            self.sbc(self.read8(addr))
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- CMP ----
        if op == 0xC9:               # CMP #imm
            value = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xC5:               # CMP zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            value = self.read8(zp)
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xD5:               # CMP zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            value = self.read8(zp)
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xCD:               # CMP abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            value = self.read8(addr)
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xDD:               # CMP abs,X
            base = self.read16(self.pc)
            addr = (base + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            value = self.read8(addr)
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0xD9:               # CMP abs,Y
            base = self.read16(self.pc)
            addr = (base + self.y) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            value = self.read8(addr)
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return cycles + (1 if self.page_crossed(base, addr) else 0)
        if op == 0xC1:               # CMP (zp,X)
            ptr = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            value = self.read8(self.read16_zp(ptr))
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xD1:               # CMP (zp),Y
            ptr = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            base = self.read16_zp(ptr)
            addr = (base + self.y) & 0xFFFF
            value = self.read8(addr)
            r = (self.a - value) & 0x1FF
            self.set_flag(0x01, self.a >= value)
            self.set_zn(r & 0xFF)
            return cycles + (1 if self.page_crossed(base, addr) else 0)

        # ---- CPX ----
        if op == 0xE0:               # CPX #imm
            value = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            r = (self.x - value) & 0x1FF
            self.set_flag(0x01, self.x >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xE4:               # CPX zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            value = self.read8(zp)
            r = (self.x - value) & 0x1FF
            self.set_flag(0x01, self.x >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xEC:               # CPX abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            value = self.read8(addr)
            r = (self.x - value) & 0x1FF
            self.set_flag(0x01, self.x >= value)
            self.set_zn(r & 0xFF)
            return

        # ---- CPY ----
        if op == 0xC0:               # CPY #imm
            value = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            r = (self.y - value) & 0x1FF
            self.set_flag(0x01, self.y >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xC4:               # CPY zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            value = self.read8(zp)
            r = (self.y - value) & 0x1FF
            self.set_flag(0x01, self.y >= value)
            self.set_zn(r & 0xFF)
            return
        if op == 0xCC:               # CPY abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            value = self.read8(addr)
            r = (self.y - value) & 0x1FF
            self.set_flag(0x01, self.y >= value)
            self.set_zn(r & 0xFF)
            return

        # ---- Stack ----
        if op == 0x48:               # PHA
            self.push8(self.a)
            return
        if op == 0x68:               # PLA
            self.a = self.pop8()
            self.set_zn(self.a)
            return
        if op == 0x08:               # PHP
            self.push8(self.p | 0x10 | 0x20)
            return
        if op == 0x28:               # PLP
            self.p = (self.pop8() | 0x20) & 0xEF | (self.p & 0x10)
            return

        # ---- Shifts (accumulator) ----
        if op == 0x0A:               # ASL A
            self.set_flag(0x01, (self.a & 0x80) != 0)
            self.a = (self.a << 1) & 0xFF
            self.set_zn(self.a)
            return
        if op == 0x4A:               # LSR A
            self.set_flag(0x01, (self.a & 0x01) != 0)
            self.a = (self.a >> 1) & 0xFF
            self.set_zn(self.a)
            return
        if op == 0x2A:               # ROL A
            c = self.get_flag(0x01)
            self.set_flag(0x01, (self.a & 0x80) != 0)
            self.a = ((self.a << 1) & 0xFF) | c
            self.set_zn(self.a)
            return
        if op == 0x6A:               # ROR A
            c = self.get_flag(0x01)
            self.set_flag(0x01, (self.a & 0x01) != 0)
            self.a = ((self.a >> 1) & 0x7F) | (c << 7)
            self.set_zn(self.a)
            return

        # ---- Shifts (memory) ----
        if op == 0x06:               # ASL zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.asl_mem(zp)
            return
        if op == 0x16:               # ASL zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.asl_mem(zp)
            return
        if op == 0x0E:               # ASL abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.asl_mem(addr)
            return
        if op == 0x1E:               # ASL abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.asl_mem(addr)
            return
        if op == 0x46:               # LSR zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.lsr_mem(zp)
            return
        if op == 0x56:               # LSR zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.lsr_mem(zp)
            return
        if op == 0x4E:               # LSR abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.lsr_mem(addr)
            return
        if op == 0x5E:               # LSR abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.lsr_mem(addr)
            return
        if op == 0x26:               # ROL zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.rol_mem(zp)
            return
        if op == 0x36:               # ROL zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.rol_mem(zp)
            return
        if op == 0x2E:               # ROL abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.rol_mem(addr)
            return
        if op == 0x3E:               # ROL abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.rol_mem(addr)
            return
        if op == 0x66:               # ROR zp
            zp = self.read8(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.ror_mem(zp)
            return
        if op == 0x76:               # ROR zp,X
            zp = (self.read8(self.pc) + self.x) & 0xFF
            self.pc = (self.pc + 1) & 0xFFFF
            self.ror_mem(zp)
            return
        if op == 0x6E:               # ROR abs
            addr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            self.ror_mem(addr)
            return
        if op == 0x7E:               # ROR abs,X
            addr = (self.read16(self.pc) + self.x) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.ror_mem(addr)
            return

        # ---- Jumps / Calls ----
        if op == 0x4C:               # JMP abs
            self.pc = self.read16(self.pc)
            return 3
        if op == 0x6C:               # JMP (indirect) with page-wrap bug
            ptr = self.read16(self.pc)
            self.pc = (self.pc + 2) & 0xFFFF
            lo = self.read8(ptr)
            hi = self.read8((ptr & 0xFF00) | ((ptr + 1) & 0x00FF))
            self.pc = lo | (hi << 8)
            return 5
        if op == 0x20:               # JSR abs
            target = self.read16(self.pc)
            ret = (self.pc + 1) & 0xFFFF
            self.pc = (self.pc + 2) & 0xFFFF
            self.push8((ret >> 8) & 0xFF)
            self.push8(ret & 0xFF)
            self.pc = target
            return 6
        if op == 0x60:               # RTS
            lo = self.pop8()
            hi = self.pop8()
            self.pc = (((hi << 8) | lo) + 1) & 0xFFFF
            return 6
        if op == 0x40:               # RTI
            self.p = (self.pop8() | 0x20) & 0xEF | (self.p & 0x10)
            lo = self.pop8()
            hi = self.pop8()
            self.pc = (hi << 8) | lo
            return 6

        # ---- Branches ----
        if op == 0xF0:               # BEQ
            return cycles + self.branch((self.p & 0x02) != 0)
        if op == 0xD0:               # BNE
            return cycles + self.branch((self.p & 0x02) == 0)
        if op == 0x10:               # BPL
            return cycles + self.branch((self.p & 0x80) == 0)
        if op == 0x30:               # BMI
            return cycles + self.branch((self.p & 0x80) != 0)
        if op == 0x90:               # BCC
            return cycles + self.branch((self.p & 0x01) == 0)
        if op == 0xB0:               # BCS
            return cycles + self.branch((self.p & 0x01) != 0)
        if op == 0x50:               # BVC
            return cycles + self.branch((self.p & 0x40) == 0)
        if op == 0x70:               # BVS
            return cycles + self.branch((self.p & 0x40) != 0)

        # ---- BRK ----
        if op == 0x00:               # BRK
            # BRK behaves as a 2-byte instruction and pushes PC+1.
            brk_pc = (self.pc + 1) & 0xFFFF
            self.push8((brk_pc >> 8) & 0xFF)
            self.push8(brk_pc & 0xFF)
            self.push8(self.p | 0x10 | 0x20)
            self.set_flag(0x04, True)   # I flag
            vector = self.read16(0xFFFE)
            if vector in (0x0000, 0xFFFF):
                # If vector is missing, avoid hard-stop.
                return 7
            self.pc = vector
            return 7

        # ---- Unimplemented opcode ----
        self.unimplemented_opcode_count += 1
        self.last_unimplemented_opcode = op
        if self.unimplemented_opcode_count <= 5 or self.unimplemented_opcode_count % 500 == 0:
            self.status.config(
                text=f"nesemu 1.0 — Warning: unknown opcode ${op:02X} at PC ${((self.pc - 1) & 0xFFFF):04X} (treated as NOP)"
            )
        # Treat as NOP (already advanced PC)
        return 2

    # ------------------------------------------------------------------
    #  Emulation Loop (Frame)
    # ------------------------------------------------------------------
    def run_frame_loop(self):
        if not self.running or self.paused:
            self.root.after(16, self.run_frame_loop)
            return

        # Execute enough CPU cycles for one frame based on TV system.
        cycles_per_frame = self.cpu_cycles_per_frame
        cycles_per_step = 1000
        remaining = cycles_per_frame
        while remaining > 0 and self.running and not self.paused:
            steps = min(remaining, cycles_per_step)
            consumed = 0
            while consumed < steps and self.running and not self.paused:
                cpu_cycles = self.cpu_step()
                if not isinstance(cpu_cycles, int) or cpu_cycles <= 0:
                    cpu_cycles = self.get_opcode_cycles(self.last_opcode)
                self.cpu_cycles_total += cpu_cycles
                # PPU runs at 3x CPU clock.
                ppu_ticks = cpu_cycles * 3
                for _ in range(ppu_ticks):
                    self.ppu_step()
                consumed += cpu_cycles
                if cpu_cycles & 1:
                    self.cpu_odd_cycle = not self.cpu_odd_cycle
            remaining -= consumed
            self.root.update_idletasks()   # allow UI to refresh

        self.frame_count += 1
        self.draw_frame()

        # Update FPS counter
        now = time.time()
        if self.frame_count % 30 == 0:
            fps = 30 / (now - self.last_time)
            self.fps_label.config(text=f"FPS: {fps:.1f}")
            self.last_time = now

        self.root.after(1, self.run_frame_loop)   # aim for 60 fps

    # ------------------------------------------------------------------
    #  Drawing (Pattern Table Viewer)
    # ------------------------------------------------------------------
    def build_palette(self):
        """Build a 64-color NES palette (sRGB approximation)."""
        # This is a common modern NES palette approximation suitable for LCD/OLED output.
        # Using full 6-bit indices removes the green-tint debug look.
        return [
            "#7C7C7C", "#0000FC", "#0000BC", "#4428BC", "#940084", "#A80020", "#A81000", "#881400",
            "#503000", "#007800", "#006800", "#005800", "#004058", "#000000", "#000000", "#000000",
            "#BCBCBC", "#0078F8", "#0058F8", "#6844FC", "#D800CC", "#E40058", "#F83800", "#E45C10",
            "#AC7C00", "#00B800", "#00A800", "#00A844", "#008888", "#000000", "#000000", "#000000",
            "#F8F8F8", "#3CBCFC", "#6888FC", "#9878F8", "#F878F8", "#F85898", "#F87858", "#FCA044",
            "#F8B800", "#B8F818", "#58D854", "#58F898", "#00E8D8", "#787878", "#000000", "#000000",
            "#FCFCFC", "#A4E4FC", "#B8B8F8", "#D8B8F8", "#F8B8F8", "#F8A4C0", "#F0D0B0", "#FCE0A8",
            "#F8D878", "#D8F878", "#B8F8B8", "#B8F8D8", "#00FCFC", "#F8D8F8", "#000000", "#000000",
        ]

    def draw_ppu_background(self):
        """Render background and return per-pixel opaque state for sprite priority."""
        base_nt = 0x2000 | ((self.ppu_ctrl & 0x03) * 0x400)
        bg_pt_base = 0x1000 if (self.ppu_ctrl & 0x10) else 0x0000
        bg_opaque = [[False] * 256 for _ in range(240)]
        scroll_x = self.ppu_scroll_x & 0xFF
        scroll_y = self.ppu_scroll_y & 0xFF
        show_left_bg = (self.ppu_mask & 0x02) != 0

        # Draw only visible NES area using PPU memory.
        for sy in range(240):
            wy = (sy + scroll_y) & 0x1FF
            nt_row = (wy >> 3) & 0x1F
            fine_y = wy & 0x07
            for sx in range(256):
                if sx < 8 and not show_left_bg:
                    pal_index = self.ppu_palette_ram[0] & 0x3F
                    color = self.palette[pal_index]
                    x = int(sx * self.scale)
                    y = int(sy * self.scale)
                    self.canvas.create_rectangle(
                        x, y, x + self.scale, y + self.scale,
                        fill=color, outline=""
                    )
                    continue

                wx = (sx + scroll_x) & 0x1FF
                nt_col = (wx >> 3) & 0x1F
                fine_x = wx & 0x07
                nt_index = nt_row * 32 + nt_col
                tile_id = self.ppu_read(base_nt + nt_index)
                tile_addr = bg_pt_base + tile_id * 16

                # Attribute table: one byte per 4x4 tile area (32x32 pixels).
                attr_addr = base_nt + 0x03C0 + ((nt_row // 4) * 8) + (nt_col // 4)
                attr = self.ppu_read(attr_addr)
                shift = ((nt_row & 0x02) << 1) | (nt_col & 0x02)
                palette_sel = (attr >> shift) & 0x03

                p0 = self.ppu_read(tile_addr + fine_y)
                p1 = self.ppu_read(tile_addr + fine_y + 8)
                bit = 7 - fine_x
                c = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1)
                if c == 0:
                    pal_index = self.ppu_palette_ram[0] & 0x3F
                else:
                    bg_opaque[sy][sx] = True
                    pal_index = self.ppu_palette_ram[(palette_sel * 4 + c) & 0x1F] & 0x3F
                color = self.palette[pal_index & 0x3F]
                x = int(sx * self.scale)
                y = int(sy * self.scale)
                self.canvas.create_rectangle(
                    x, y, x + self.scale, y + self.scale,
                    fill=color, outline=""
                )
        return bg_opaque

    def draw_ppu_sprites(self, bg_opaque):
        """Render sprites from OAM with priority/flip and sprite-0 hit approximation."""
        show_left_sprites = (self.ppu_mask & 0x04) != 0
        sprite_pt_base = 0x1000 if (self.ppu_ctrl & 0x08) else 0x0000
        sprite_8x16 = (self.ppu_ctrl & 0x20) != 0
        self.ppu_status &= ~0x40  # clear sprite 0 hit before calculating this frame

        # Back-to-front for correct priority among sprites.
        for i in range(63, -1, -1):
            base = i * 4
            y = self.ppu_oam[base] + 1
            tile = self.ppu_oam[base + 1]
            attr = self.ppu_oam[base + 2]
            x = self.ppu_oam[base + 3]
            flip_h = (attr & 0x40) != 0
            flip_v = (attr & 0x80) != 0
            behind_bg = (attr & 0x20) != 0
            pal_sel = attr & 0x03

            height = 16 if sprite_8x16 else 8
            if y >= 240 or y <= -height:
                continue

            for row in range(height):
                sy = y + row
                if sy < 0 or sy >= 240:
                    continue
                ry = (height - 1 - row) if flip_v else row

                if sprite_8x16:
                    bank = (tile & 0x01) * 0x1000
                    tile_index = tile & 0xFE
                    if ry >= 8:
                        tile_index += 1
                        ry -= 8
                    tile_addr = bank + tile_index * 16
                else:
                    tile_addr = sprite_pt_base + tile * 16

                p0 = self.ppu_read(tile_addr + ry)
                p1 = self.ppu_read(tile_addr + ry + 8)
                for col in range(8):
                    sx = x + col
                    if sx < 0 or sx >= 256:
                        continue
                    if sx < 8 and not show_left_sprites:
                        continue
                    rx = col if flip_h else (7 - col)
                    c = ((p0 >> rx) & 1) | (((p1 >> rx) & 1) << 1)
                    if c == 0:
                        continue

                    if i == 0 and bg_opaque[sy][sx] and (self.ppu_mask & 0x08):
                        # Approximate sprite-0 hit used by SMB1 status-bar split logic.
                        self.ppu_status |= 0x40

                    if behind_bg and bg_opaque[sy][sx]:
                        continue

                    pal_addr = 0x10 + pal_sel * 4 + c
                    pal_index = self.ppu_palette_ram[self.ppu_palette_addr(0x3F00 + pal_addr)] & 0x3F
                    color = self.palette[pal_index]
                    px = int(sx * self.scale)
                    py = int(sy * self.scale)
                    self.canvas.create_rectangle(
                        px, py, px + self.scale, py + self.scale,
                        fill=color, outline=""
                    )

    def draw_frame(self):
        """Draw current frame from PPU state, fallback to CHR viewer."""
        self.canvas.delete("all")

        bg_enabled = (self.ppu_mask & 0x08) != 0
        spr_enabled = (self.ppu_mask & 0x10) != 0
        if bg_enabled and (self.chr_rom or self.chr_ram is not None):
            bg_opaque = self.draw_ppu_background()
            if spr_enabled:
                self.draw_ppu_sprites(bg_opaque)
        elif not self.chr_rom and self.chr_ram is None:
            self.canvas.create_text(
                self.screen_width // 2, self.screen_height // 2,
                text="No CHR ROM loaded.\nOnly pattern table viewer is shown.",
                fill="white", font=("Courier", 10), justify=tk.CENTER
            )
        else:
            # Draw pattern table 0 (first 256 tiles) as a grid
            tile_pixels = 8
            cols = 16
            rows = 16
            tile_width = tile_pixels * self.scale
            tile_height = tile_pixels * self.scale

            # Center the grid
            grid_width = cols * tile_width
            grid_height = rows * tile_height
            x_offset = max(0, (self.screen_width - grid_width) // 2)
            y_offset = max(0, (self.screen_height - grid_height) // 2)

            for tile_idx in range(256):
                if tile_idx * 16 >= len(self.chr_rom):
                    break
                row = tile_idx // cols
                col = tile_idx % cols
                x = x_offset + col * tile_width
                y = y_offset + row * tile_height

                tile_data = self.chr_rom[tile_idx * 16:(tile_idx + 1) * 16]
                for py in range(8):
                    p0 = tile_data[py]
                    p1 = tile_data[py + 8]
                    for px in range(8):
                        bit = 7 - px
                        c = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1)
                        # Debug pattern table grayscale ramp (uses actual NES palette entries).
                        debug_lut = (0x0F, 0x00, 0x10, 0x20)
                        color = self.palette[debug_lut[c]]
                        x1 = x + px * self.scale
                        y1 = y + py * self.scale
                        self.canvas.create_rectangle(
                            x1, y1, x1 + self.scale, y1 + self.scale,
                            fill=color, outline=""
                        )

        # Overlay text (NESEMU By A.C Holdings style)
        self.canvas.create_text(
            self.screen_width // 2, 20,
            text=f"FRAME {self.frame_count} | nesemu 1.0",
            fill="#00ff00", font=("Courier", 12, "bold")
        )

        cpu_line = (f"PC:${self.pc:04X} OP:${self.last_opcode:02X} "
                    f"A:{self.a:02X} X:{self.x:02X} Y:{self.y:02X} "
                    f"SP:{self.sp:02X} P:{self.p:02X}")
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height - 20,
            text=cpu_line, fill="#00ff88", font=("Courier", 10)
        )

        if self.unimplemented_opcode_count > 0:
            warn = f"Unknown opcodes: {self.unimplemented_opcode_count}"
            if self.last_unimplemented_opcode is not None:
                warn += f" (last ${self.last_unimplemented_opcode:02X})"
            self.canvas.create_text(
                self.screen_width // 2, self.screen_height - 38,
                text=warn, fill="#ffaa44", font=("Courier", 9)
            )
        ppu_line = (
            f"PPU SL:{self.ppu_scanline:03d} DOT:{self.ppu_cycle:03d} "
            f"CTRL:{self.ppu_ctrl:02X} MASK:{self.ppu_mask:02X} STATUS:{self.ppu_status:02X}"
        )
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height - 55,
            text=ppu_line, fill="#66ccff", font=("Courier", 9)
        )
        controls_line = "P1: Arrows Move | Z=A | X=B | Enter=Start | BackSpace=Select"
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height - 72,
            text=controls_line, fill="#BBBBBB", font=("Courier", 8)
        )

    # ------------------------------------------------------------------
    #  Event Handlers
    # ------------------------------------------------------------------
    def key_press(self, event):
        action = self.get_action_for_key(event.keysym)
        if action is not None:
            self.action_state[action] = True
            self.update_controller_state()

    def key_release(self, event):
        action = self.get_action_for_key(event.keysym)
        if action is not None:
            self.action_state[action] = False
            self.update_controller_state()

    def on_frame_resize(self, event):
        """Resize canvas to maintain aspect ratio."""
        # Recalculate scale based on frame size, keep 256x240 aspect
        new_width = event.width
        new_height = event.height
        scale_x = new_width / 256
        scale_y = new_height / 240
        self.scale = min(scale_x, scale_y)
        self.screen_width = int(256 * self.scale)
        self.screen_height = int(240 * self.scale)
        self.canvas.config(width=self.screen_width, height=self.screen_height)

    def dummy_nesemu(self):
        messagebox.showinfo("NESEMU By A.C Holdings / nesemu 1.0",
                            "This menu item is exactly like NESEMU By A.C Holdings.\n\nFull emulation core ready for your Cython code!")

    def get_roadmap_markdown(self):
        return (
            "# NESEMU By A.C Holdings Roadmap\n\n"
            "## Current\n"
            "- Python-only GUI frontend and emulation skeleton\n"
            "- iNES/NES 2.0 header parsing\n"
            "- Mapper 0 (NROM) boot path\n"
            "- Partial 6502 instruction support\n"
            "- PPU background/pattern-table rendering path\n\n"
            "## Next Milestones\n"
            "1. Complete CPU opcode + cycle correctness\n"
            "2. Improve PPU timing accuracy and sprite pipeline\n"
            "3. Add APU timing + basic audio output\n"
            "4. Add mapper support beyond NROM\n"
            "5. Add automated ROM test-suite runner\n\n"
            "## Notes\n"
            "- This roadmap is embedded in the Python source.\n"
            "- No external roadmap/PR file is required.\n"
        )

    def show_roadmap(self):
        win = tk.Toplevel(self.root)
        win.title("nesemu Project Roadmap")
        win.geometry("780x560")
        win.configure(bg="#222222")
        win.transient(self.root)

        container = tk.Frame(win, bg="#222222")
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        text = tk.Text(
            container,
            wrap=tk.WORD,
            bg="#101010",
            fg="#D6FFD6",
            insertbackground="#D6FFD6",
            font=("Courier", 10),
            relief=tk.FLAT
        )
        scroll = tk.Scrollbar(container, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text.insert("1.0", self.get_roadmap_markdown())
        text.configure(state=tk.DISABLED)

    def show_about(self):
        messagebox.showinfo(
            "nesemu 1.0 (NESEMU By A.C Holdings GUI)",
            "nesemu 1.0 - NESEMU By A.C Holdings Edition\n\n"
            "✅ 600×400 window (resizable)\n"
            "✅ Exact NESEMU By A.C Holdings menu + toolbar\n"
            "✅ REAL .nes ROM loading + iNES header parsing\n"
            "✅ Keyboard input (Arrow keys, Z/A, X/B, Enter, Backspace)\n"
            "✅ Live FPS counter\n"
            "✅ Cython-ready emulation loop\n\n"
            "You now have a real-looking NES emulator that actually loads and parses any .nes ROM.\n"
            "Drop your full 6502 + PPU Cython code into 'run_frame_loop' and it becomes 100% real!"
        )

    def on_close(self):
        if messagebox.askokcancel("Exit nesemu 1.0", "Quit NESEMU By A.C Holdings-style emulator?"):
            self.root.destroy()


# ----------------------------------------------------------------------
#  Main Entry Point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = NesEmuFceuxStyle()
    app.root.mainloop()
