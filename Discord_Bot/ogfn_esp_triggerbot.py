"""
OGFN Private Server - ESP + Triggerbot System
For educational purposes with private/non-anti-cheat environments only
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import math
import pyautogui
import keyboard
import win32api
import win32con
from dataclasses import dataclass
from typing import List, Tuple, Optional
import json
import os

# ==================== CONFIGURATION ====================
@dataclass
class Config:
    """Configuration settings for ESP and Triggerbot"""
    # ESP Settings
    esp_enabled: bool = True
    esp_box_color: str = "#FF0000"  # Red
    esp_skeleton_color: str = "#00FF00"  # Green
    esp_text_color: str = "#FFFFFF"  # White
    esp_distance_color: str = "#FFFF00"  # Yellow
    esp_max_distance: int = 300
    esp_show_health: bool = True
    esp_show_names: bool = True
    esp_show_distance: bool = True
    esp_show_bones: bool = True
    
    # Triggerbot Settings
    triggerbot_enabled: bool = False
    trigger_key: str = 'shift'  # Hold this key to activate
    trigger_delay_ms: int = 50  # Human-like reaction delay
    trigger_fov: int = 50  # Field of view for trigger
    trigger_hitbox: str = 'chest'  # 'head', 'chest', 'any'
    
    # Aimbot Settings
    aimbot_enabled: bool = False
    aimbot_key: str = 'ctrl'
    aimbot_smoothness: float = 5.0
    aimbot_fov: int = 100
    aimbot_target_bone: str = 'head'
    
    # Menu Settings
    menu_key: str = 'insert'
    menu_visible: bool = True


# ==================== PLAYER DATA ====================
@dataclass
class Player:
    """Represents a player in the game"""
    id: int
    name: str
    team: int
    health: int
    max_health: int
    x: float
    y: float
    z: float
    screen_x: Optional[float] = None
    screen_y: Optional[float] = None
    distance: Optional[float] = None
    
    # Bone positions for skeleton ESP
    bones: dict = None
    
    def __post_init__(self):
        self.bones = {
            'head': (self.x, self.y + 10, self.z),
            'neck': (self.x, self.y + 8, self.z),
            'chest': (self.x, self.y + 6, self.z),
            'waist': (self.x, self.y + 3, self.z),
            'left_shoulder': (self.x - 2, self.y + 8, self.z),
            'right_shoulder': (self.x + 2, self.y + 8, self.z),
            'left_elbow': (self.x - 3, self.y + 6, self.z),
            'right_elbow': (self.x + 3, self.y + 6, self.z),
            'left_hand': (self.x - 4, self.y + 4, self.z),
            'right_hand': (self.x + 4, self.y + 4, self.z),
            'left_knee': (self.x - 1, self.y - 3, self.z),
            'right_knee': (self.x + 1, self.y - 3, self.z),
            'left_foot': (self.x - 1, self.y - 8, self.z),
            'right_foot': (self.x + 1, self.y - 8, self.z)
        }


# ==================== GAME WORLD SIMULATION ====================
class GameWorld:
    """Simulates game world with players for testing"""
    
    def __init__(self):
        self.players = []
        self.local_player = Player(
            id=0, name="YOU", team=1, health=100, max_health=100,
            x=0, y=0, z=0
        )
        self.generate_test_players()
        
    def generate_test_players(self, count=10):
        """Generate random test players"""
        self.players = []
        for i in range(1, count + 1):
            player = Player(
                id=i,
                name=f"Player{i}",
                team=random.choice([1, 2]),
                health=random.randint(0, 100),
                max_health=100,
                x=random.uniform(-200, 200),
                y=random.uniform(-200, 200),
                z=random.uniform(-50, 50)
            )
            self.players.append(player)
            
    def update_positions(self):
        """Update player positions (simulate movement)"""
        for player in self.players:
            player.x += random.uniform(-2, 2)
            player.y += random.uniform(-2, 2)
            player.z += random.uniform(-1, 1)
            
            # Update distance from local player
            dx = player.x - self.local_player.x
            dy = player.y - self.local_player.y
            dz = player.z - self.local_player.z
            player.distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Simple 2D screen projection (mock)
            if player.distance > 0:
                player.screen_x = 400 + (dx / player.distance) * 200
                player.screen_y = 300 + (dy / player.distance) * 200
                
    def world_to_screen(self, x, y, z):
        """Convert 3D world coordinates to 2D screen coordinates"""
        # This is a simplified version - real implementation would use view/projection matrices
        dx = x - self.local_player.x
        dy = y - self.local_player.y
        dz = z - self.local_player.z
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if distance > 0:
            screen_x = 400 + (dx / distance) * 200
            screen_y = 300 + (dy / distance) * 200
            return (screen_x, screen_y)
        return None


# ==================== ESP RENDERER ====================
class ESPRenderer:
    """Handles rendering of ESP elements"""
    
    def __init__(self, canvas, config):
        self.canvas = canvas
        self.config = config
        self.esp_elements = []
        
    def clear(self):
        """Clear all ESP elements"""
        for element in self.esp_elements:
            self.canvas.delete(element)
        self.esp_elements = []
        
    def render_player(self, player):
        """Render ESP for a single player"""
        if not player.screen_x or not player.screen_y:
            return
            
        # Don't render if beyond max distance
        if player.distance > self.config.esp_max_distance:
            return
            
        # Determine color based on team
        if player.team == 1:
            color = "#FF0000"  # Red team
        else:
            color = "#0000FF"  # Blue team
            
        # Render 2D box
        if self.config.esp_enabled:
            box_size = max(30, 200 / max(player.distance, 1))
            x1 = player.screen_x - box_size
            y1 = player.screen_y - box_size
            x2 = player.screen_x + box_size
            y2 = player.screen_y + box_size
            
            # Box outline
            box = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=color,
                width=2
            )
            self.esp_elements.append(box)
            
            # Health bar
            if self.config.esp_show_health:
                health_height = 5
                health_width = box_size * 2
                health_percent = player.health / player.max_health
                
                # Background
                health_bg = self.canvas.create_rectangle(
                    x1 - 2, y1 - health_height - 5,
                    x1 + health_width + 2, y1 - 5,
                    fill="black",
                    outline="white"
                )
                self.esp_elements.append(health_bg)
                
                # Health fill
                health_fill = self.canvas.create_rectangle(
                    x1, y1 - health_height - 3,
                    x1 + (health_width * health_percent), y1 - 7,
                    fill="green",
                    outline=""
                )
                self.esp_elements.append(health_fill)
                
            # Player name
            if self.config.esp_show_names:
                name_text = self.canvas.create_text(
                    player.screen_x,
                    y2 + 15,
                    text=player.name,
                    fill="white",
                    font=("Arial", 10, "bold")
                )
                self.esp_elements.append(name_text)
                
            # Distance
            if self.config.esp_show_distance:
                dist_text = self.canvas.create_text(
                    player.screen_x,
                    y2 + 30,
                    text=f"{int(player.distance)}m",
                    fill="yellow",
                    font=("Arial", 8)
                )
                self.esp_elements.append(dist_text)
                
        # Render skeleton ESP
        if self.config.esp_show_bones:
            self.render_skeleton(player, color)
            
    def render_skeleton(self, player, color):
        """Render skeleton ESP for player"""
        bones_to_draw = [
            ('head', 'neck'),
            ('neck', 'chest'),
            ('chest', 'waist'),
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_elbow'),
            ('right_shoulder', 'right_elbow'),
            ('left_elbow', 'left_hand'),
            ('right_elbow', 'right_hand'),
            ('waist', 'left_knee'),
            ('waist', 'right_knee'),
            ('left_knee', 'left_foot'),
            ('right_knee', 'right_foot')
        ]
        
        for start_bone, end_bone in bones_to_draw:
            if start_bone in player.bones and end_bone in player.bones:
                start_pos = player.bones[start_bone]
                end_pos = player.bones[end_bone]
                
                # Convert to screen coordinates
                start_screen = GameWorld().world_to_screen(*start_pos)
                end_screen = GameWorld().world_to_screen(*end_pos)
                
                if start_screen and end_screen:
                    line = self.canvas.create_line(
                        start_screen[0], start_screen[1],
                        end_screen[0], end_screen[1],
                        fill=color,
                        width=2
                    )
                    self.esp_elements.append(line)


# ==================== TRIGGERBOT ====================
class Triggerbot:
    """Handles triggerbot functionality"""
    
    def __init__(self, config, game_world):
        self.config = config
        self.game_world = game_world
        self.active = False
        self.trigger_thread = None
        
    def start(self):
        """Start the triggerbot in a separate thread"""
        if not self.trigger_thread or not self.trigger_thread.is_alive():
            self.active = True
            self.trigger_thread = threading.Thread(target=self._trigger_loop)
            self.trigger_thread.daemon = True
            self.trigger_thread.start()
            
    def stop(self):
        """Stop the triggerbot"""
        self.active = False
        
    def _trigger_loop(self):
        """Main triggerbot loop"""
        while self.active:
            if self.config.triggerbot_enabled:
                if keyboard.is_pressed(self.config.trigger_key):
                    self._check_and_shoot()
            time.sleep(0.01)  # Prevent CPU overload
            
    def _check_and_shoot(self):
        """Check if enemy is in crosshair and shoot"""
        # Get mouse position (crosshair location)
        mouse_x, mouse_y = pyautogui.position()
        
        # Check each player
        for player in self.game_world.players:
            if player.team == self.game_world.local_player.team:
                continue  # Skip teammates
                
            if not player.screen_x or not player.screen_y:
                continue
                
            # Calculate distance from crosshair to player
            distance = math.sqrt(
                (mouse_x - player.screen_x)**2 + 
                (mouse_y - player.screen_y)**2
            )
            
            # Check if within trigger FOV
            if distance <= self.config.trigger_fov:
                # Add human-like delay
                time.sleep(self.config.trigger_delay_ms / 1000.0)
                
                # Shoot!
                self._simulate_shot()
                break
                
    def _simulate_shot(self):
        """Simulate mouse click for shooting"""
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


# ==================== MAIN MENU/GUI ====================
class OGFNMenu:
    """Main menu/GUI for ESP and Triggerbot controls"""
    
    def __init__(self):
        self.config = Config()
        self.game_world = GameWorld()
        
        # Setup main window
        self.root = tk.Tk()
        self.root.title("OGFN Private Server Tools")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        # ESP Canvas for overlay
        self.esp_canvas = tk.Canvas(
            self.root,
            width=800,
            height=400,
            bg='black',
            highlightthickness=0
        )
        self.esp_canvas.pack(pady=10)
        
        # ESP Renderer
        self.esp_renderer = ESPRenderer(self.esp_canvas, self.config)
        
        # Triggerbot
        self.triggerbot = Triggerbot(self.config, self.game_world)
        
        # Create control panels
        self.create_control_panels()
        
        # Start update loop
        self.update_esp()
        
        # Bind hotkey for menu
        keyboard.on_press_key(self.config.menu_key, lambda _: self.toggle_menu())
        
    def create_control_panels(self):
        """Create the control interface"""
        # Main control frame
        control_frame = tk.Frame(self.root, bg='#2a2a2a')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # ESP Controls
        esp_frame = tk.LabelFrame(
            control_frame,
            text="ESP Controls",
            bg='#2a2a2a',
            fg='white'
        )
        esp_frame.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.Y)
        
        self.esp_var = tk.BooleanVar(value=self.config.esp_enabled)
        tk.Checkbutton(
            esp_frame,
            text="Enable ESP",
            variable=self.esp_var,
            command=self.toggle_esp,
            bg='#2a2a2a',
            fg='white',
            selectcolor='#2a2a2a'
        ).pack(anchor=tk.W)
        
        tk.Label(esp_frame, text="Box Color:", bg='#2a2a2a', fg='white').pack(anchor=tk.W)
        self.box_color_entry = tk.Entry(esp_frame, width=10)
        self.box_color_entry.insert(0, self.config.esp_box_color)
        self.box_color_entry.pack(anchor=tk.W)
        
        # Triggerbot Controls
        trigger_frame = tk.LabelFrame(
            control_frame,
            text="Triggerbot Controls",
            bg='#2a2a2a',
            fg='white'
        )
        trigger_frame.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.Y)
        
        self.trigger_var = tk.BooleanVar(value=self.config.triggerbot_enabled)
        tk.Checkbutton(
            trigger_frame,
            text="Enable Triggerbot",
            variable=self.trigger_var,
            command=self.toggle_triggerbot,
            bg='#2a2a2a',
            fg='white',
            selectcolor='#2a2a2a'
        ).pack(anchor=tk.W)
        
        tk.Label(trigger_frame, text="Trigger Key:", bg='#2a2a2a', fg='white').pack(anchor=tk.W)
        self.trigger_key_entry = tk.Entry(trigger_frame, width=10)
        self.trigger_key_entry.insert(0, self.config.trigger_key)
        self.trigger_key_entry.pack(anchor=tk.W)
        
        tk.Label(trigger_frame, text="Delay (ms):", bg='#2a2a2a', fg='white').pack(anchor=tk.W)
        self.delay_scale = tk.Scale(
            trigger_frame,
            from_=0,
            to=200,
            orient=tk.HORIZONTAL,
            bg='#2a2a2a',
            fg='white',
            highlightbackground='#2a2a2a'
        )
        self.delay_scale.set(self.config.trigger_delay_ms)
        self.delay_scale.pack(anchor=tk.W)
        
        tk.Label(trigger_frame, text="FOV:", bg='#2a2a2a', fg='white').pack(anchor=tk.W)
        self.fov_scale = tk.Scale(
            trigger_frame,
            from_=10,
            to=200,
            orient=tk.HORIZONTAL,
            bg='#2a2a2a',
            fg='white',
            highlightbackground='#2a2a2a'
        )
        self.fov_scale.set(self.config.trigger_fov)
        self.fov_scale.pack(anchor=tk.W)
        
        # Aimbot Controls
        aim_frame = tk.LabelFrame(
            control_frame,
            text="Aimbot Controls",
            bg='#2a2a2a',
            fg='white'
        )
        aim_frame.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.Y)
        
        self.aim_var = tk.BooleanVar(value=self.config.aimbot_enabled)
        tk.Checkbutton(
            aim_frame,
            text="Enable Aimbot",
            variable=self.aim_var,
            command=self.toggle_aimbot,
            bg='#2a2a2a',
            fg='white',
            selectcolor='#2a2a2a'
        ).pack(anchor=tk.W)
        
        tk.Label(aim_frame, text="Smoothness:", bg='#2a2a2a', fg='white').pack(anchor=tk.W)
        self.smooth_scale = tk.Scale(
            aim_frame,
            from_=1,
            to=20,
            orient=tk.HORIZONTAL,
            bg='#2a2a2a',
            fg='white',
            highlightbackground='#2a2a2a'
        )
        self.smooth_scale.set(self.config.aimbot_smoothness)
        self.smooth_scale.pack(anchor=tk.W)
        
        # Save/Load buttons
        button_frame = tk.Frame(self.root, bg='#1a1a1a')
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Save Config",
            command=self.save_config,
            bg='#4a4a4a',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Load Config",
            command=self.load_config,
            bg='#4a4a4a',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Generate Test Players",
            command=self.generate_players,
            bg='#4a4a4a',
            fg='white'
        ).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready - Press INSERT to toggle menu",
            bg='#1a1a1a',
            fg='#888888'
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def toggle_esp(self):
        """Toggle ESP on/off"""
        self.config.esp_enabled = self.esp_var.get()
        self.update_status()
        
    def toggle_triggerbot(self):
        """Toggle triggerbot on/off"""
        self.config.triggerbot_enabled = self.trigger_var.get()
        if self.config.triggerbot_enabled:
            self.triggerbot.start()
            self.update_status("Triggerbot activated")
        else:
            self.triggerbot.stop()
            self.update_status("Triggerbot deactivated")
            
    def toggle_aimbot(self):
        """Toggle aimbot on/off"""
        self.config.aimbot_enabled = self.aim_var.get()
        self.update_status()
        
    def toggle_menu(self):
        """Toggle menu visibility"""
        self.config.menu_visible = not self.config.menu_visible
        if self.config.menu_visible:
            self.root.deiconify()
        else:
            self.root.withdraw()
            
    def update_esp(self):
        """Update ESP display"""
        # Update config from GUI
        self.config.esp_box_color = self.box_color_entry.get()
        self.config.trigger_key = self.trigger_key_entry.get()
        self.config.trigger_delay_ms = self.delay_scale.get()
        self.config.trigger_fov = self.fov_scale.get()
        self.config.aimbot_smoothness = self.smooth_scale.get()
        
        # Update game world
        self.game_world.update_positions()
        
        # Clear and redraw ESP
        self.esp_renderer.clear()
        
        if self.config.esp_enabled:
            for player in self.game_world.players:
                self.esp_renderer.render_player(player)
                
        # Schedule next update
        self.root.after(50, self.update_esp)
        
    def update_status(self, message=None):
        """Update status bar"""
        if message:
            self.status_label.config(text=message)
        else:
            esp_status = "ON" if self.config.esp_enabled else "OFF"
            trigger_status = "ON" if self.config.triggerbot_enabled else "OFF"
            aim_status = "ON" if self.config.aimbot_enabled else "OFF"
            self.status_label.config(
                text=f"ESP: {esp_status} | Triggerbot: {trigger_status} | Aimbot: {aim_status}"
            )
            
    def generate_players(self):
        """Generate new test players"""
        self.game_world.generate_test_players()
        self.update_status("Generated new test players")
        
    def save_config(self):
        """Save configuration to file"""
        config_data = {
            'esp_enabled': self.config.esp_enabled,
            'esp_box_color': self.config.esp_box_color,
            'trigger_enabled': self.config.triggerbot_enabled,
            'trigger_key': self.config.trigger_key,
            'trigger_delay_ms': self.config.trigger_delay_ms,
            'trigger_fov': self.config.trigger_fov,
            'aimbot_enabled': self.config.aimbot_enabled,
            'aimbot_smoothness': self.config.aimbot_smoothness
        }
        
        with open('ogfn_config.json', 'w') as f:
            json.dump(config_data, f, indent=4)
            
        self.update_status("Configuration saved")
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists('ogfn_config.json'):
            with open('ogfn_config.json', 'r') as f:
                config_data = json.load(f)
                
            self.config.esp_enabled = config_data.get('esp_enabled', True)
            self.config.esp_box_color = config_data.get('esp_box_color', '#FF0000')
            self.config.triggerbot_enabled = config_data.get('trigger_enabled', False)
            self.config.trigger_key = config_data.get('trigger_key', 'shift')
            self.config.trigger_delay_ms = config_data.get('trigger_delay_ms', 50)
            self.config.trigger_fov = config_data.get('trigger_fov', 50)
            self.config.aimbot_enabled = config_data.get('aimbot_enabled', False)
            self.config.aimbot_smoothness = config_data.get('aimbot_smoothness', 5.0)
            
            # Update GUI elements
            self.esp_var.set(self.config.esp_enabled)
            self.trigger_var.set(self.config.triggerbot_enabled)
            self.aim_var.set(self.config.aimbot_enabled)
            self.box_color_entry.delete(0, tk.END)
            self.box_color_entry.insert(0, self.config.esp_box_color)
            self.trigger_key_entry.delete(0, tk.END)
            self.trigger_key_entry.insert(0, self.config.trigger_key)
            self.delay_scale.set(self.config.trigger_delay_ms)
            self.fov_scale.set(self.config.trigger_fov)
            self.smooth_scale.set(self.config.aimbot_smoothness)
            
            self.update_status("Configuration loaded")
            
    def run(self):
        """Run the main application"""
        self.root.mainloop()


# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    print("=" * 50)
    print("OGFN Private Server Tools")
    print("ESP + Triggerbot System")
    print("=" * 50)
    print("\nFeatures:")
    print("  • ESP with 2D boxes, health bars, player names, distance")
    print("  • Skeleton ESP (bone display)")
    print("  • Triggerbot with adjustable FOV and delay")
    print("  • Aimbot with smoothness control")
    print("  • Fully customizable hotkeys")
    print("  • Save/load configuration")
    print("\nControls:")
    print("  • INSERT - Toggle menu visibility")
    print("  • SHIFT - Hold to activate triggerbot")
    print("  • CTRL - Hold to activate aimbot")
    print("\nDISCLAIMER: For private/offline servers only!")
    print("=" * 50)
    
    # Install required packages if missing
    required_packages = ['pyautogui', 'keyboard', 'pywin32']
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Installing {package}...")
            os.system(f"pip install {package}")
            
    # Run the application
    app = OGFNMenu()
    app.run()