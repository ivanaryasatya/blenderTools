import os
import subprocess
import bpy
import json

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_directory(current_path):
    """Menampilkan isi direktori dan mengembalikan daftar item."""
    try:
        items = os.listdir(current_path)
    except PermissionError:
        print("\n[!] Access denied to this folder.")
        return []

    # Filter: hanya tampilkan folder atau file .blend
    filtered_items = [
        item for item in items 
        if os.path.isdir(os.path.join(current_path, item)) or item.endswith('.blend')
    ]
    filtered_items.sort()
    return filtered_items

def file_browser(start_path):
    """Navigasi folder secara interaktif menggunakan angka."""
    current_path = os.path.abspath(start_path)
    
    while True:
        clear_screen()
        print(f"--- Blender File Browser ---")
        print(f"Lokasi saat ini: {current_path}\n")
        print(f"--- Blender File Browser ---")
        print(f"Current location: {current_path}\n")
        
        items = list_directory(current_path)
        
        print("0. [..] Go back to previous folder")
        for i, item in enumerate(items, 1):
            prefix = "[FOLDER]" if os.path.isdir(os.path.join(current_path, item)) else "[FILE  ]"
            print(f"{i}. {prefix} {item}")
        
        print("\nq. Cancel and return to main menu")
        
        choice = input("\nSelect number: ").strip()
        
        if choice.lower() == 'q':
            return None
        
        if choice == '0':
            current_path = os.path.dirname(current_path)
            continue
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                selected_item = items[idx]
                full_path = os.path.join(current_path, selected_item)
                
                if os.path.isdir(full_path):
                    current_path = full_path
                elif selected_item.endswith('.blend'):
                    return full_path
            else:
                print("\n[!] Invalid choice.")
                input("Press Enter to continue...")
        except ValueError:
            print("\n[!] Please enter a valid number.")
            input("Press Enter to continue...")

def parse_frames(frame_str):
    """Mengonversi string '1, 5, 10-15' menjadi list integer unik dan terurut."""
    frames = []
    if not frame_str:
        return frames
    # Bersihkan spasi dan pisahkan berdasarkan koma
    parts = frame_str.replace(" ", "").split(",")
    for part in parts:
        try:
            if "-" in part:
                start, end = part.split("-")
                frames.extend(range(int(start), int(end) + 1))
            else:
                frames.append(int(part))
        except (ValueError, TypeError):
            continue
    return sorted(list(set(frames)))

def render_blender(filepath, settings):
    """Menjalankan proses render menggunakan perintah blender (CLI)."""
    clear_screen()
    print(f"--- Starting Render ---")
    print(f"File: {filepath}\n")
    
    # Membangun argumen perintah berdasarkan settings
    args = []
    if settings['scene']:
        args.append(f'-S "{settings["scene"]}"')
    if settings['engine']:
        args.append(f'-E {settings["engine"]}')
    
    # Membangun perintah python-expr untuk pengaturan yang tidak ada flag CLI-nya
    py_parts = ["import bpy"]
    if settings['overwrite'] is not None:
        py_parts.append(f"bpy.context.scene.render.use_overwrite={settings['overwrite']}")
    if settings['placeholder'] is not None:
        py_parts.append(f"bpy.context.scene.render.use_placeholder={settings['placeholder']}")
    
    if settings['samples']:
        if settings['engine'] == "CYCLES":
            py_parts.append(f"bpy.context.scene.cycles.samples={settings['samples']}")
        elif settings['engine'] == "BLENDER_EEVEE":
            py_parts.append(f"bpy.context.scene.eevee.taa_render_samples={settings['samples']}")
        else:
            py_parts.append(f"try: bpy.context.scene.cycles.samples={settings['samples']}\nexcept: pass")
            py_parts.append(f"try: bpy.context.scene.eevee.taa_render_samples={settings['samples']}\nexcept: pass")

    if len(py_parts) > 1:
        py_cmd = "; ".join(py_parts)
        args.append(f'--python-expr "{py_cmd}"')

    if settings['frames']:
        frame_list = parse_frames(settings['frames'])
        for f in frame_list:
            args.append(f"-f {f}")
    else:
        args.append("-a")

    render_args = " ".join(args)
    command = f'blender -b "{filepath}" {render_args}'
    
    print(f"Executing: {command}")
    print("Processing... (Press Ctrl+C to stop)\n")
    
    try:
        subprocess.run(command, shell=True)
        print("\n[+] Render complete!")
    except Exception as e:
        print(f"\n[!] An error occurred during render: {e}")
    
    input("\nPress Enter to return to menu...")

def get_blender_scenes(filepath):
    """Mendapatkan daftar scene dari file .blend menggunakan bpy.data.libraries.load."""
    if not os.path.exists(filepath):
        return []
    try:
        # Membaca daftar scene tanpa membuka file secara penuh
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            return data_from.scenes
    except Exception as e:
        print(f"\n[!] Failed to retrieve scenes: {e}")
        return []

def render_settings_menu(filepath):
    """Menu untuk mengatur parameter render sebelum eksekusi."""
    settings = {
        "frames": None,
        "engine": None,
        "samples": None,
        "scene": None,
        "overwrite": None,
        "placeholder": None,
    }

    while True:
        clear_screen()
        print(f"--- RENDER CONFIGURATION: {os.path.basename(filepath)} ---")
        print(f"1. Frame Selection: {settings['frames'] or 'Default (All Animation)'}")
        print(f"2. Render Engine  : {settings['engine'] or 'Default (.blend)'}")
        print(f"3. Samples        : {settings['samples'] or 'Default (.blend)'}")
        print(f"4. Scene Name     : {settings['scene'] or 'Default (.blend)'}")
        print(f"5. Overwrite      : {settings['overwrite'] if settings['overwrite'] is not None else 'Default (.blend)'}")
        print(f"6. Placeholder    : {settings['placeholder'] if settings['placeholder'] is not None else 'Default (.blend)'}")
        print("-" * 30)
        print("0. CONFIRM & RENDER")
        print("q. Back to Browser")

        choice = input("\nSelect number to edit (or 0 to proceed): ").strip().lower()

        if choice == '0':
            render_blender(filepath, settings)
            break
        elif choice == 'q':
            break
        elif choice == '1':
            settings['frames'] = input("Enter Frames (e.g.: 1,5,8,30-50): ")
        elif choice == '2':
            print("\n1. CYCLES\n2. BLENDER_EEVEE\n3. BLENDER_WORKBENCH")
            eng = input("Select Engine (1-3): ")
            engines = {"1": "CYCLES", "2": "BLENDER_EEVEE", "3": "BLENDER_WORKBENCH"}
            settings['engine'] = engines.get(eng, settings['engine'])
        elif choice == '3':
            settings['samples'] = input("Enter Sample Count: ")
        elif choice == '4':
            scenes = get_blender_scenes(filepath)
            if scenes:
                print("\n--- SCENE LIST ---")
                for i, scene_name in enumerate(scenes, 1):
                    print(f"{i}. {scene_name}")
                
                s_choice = input(f"\nSelect scene number (1-{len(scenes)}): ")
                try:
                    idx = int(s_choice) - 1
                    if 0 <= idx < len(scenes):
                        settings['scene'] = scenes[idx]
                    else:
                        print("[!] Choice out of range.")
                except ValueError:
                    print("[!] Please enter a valid number.")
            else:
                print("[!] Could not find scenes or file is corrupted.")
                input("Press Enter to continue...")
        elif choice == '5':
            val = input("Overwrite? (y/n/default): ").lower()
            settings['overwrite'] = True if val == 'y' else False if val == 'n' else None
        elif choice == '6':
            val = input("Use Placeholder? (y/n/default): ").lower()
            settings['placeholder'] = True if val == 'y' else False if val == 'n' else None

def load_config():
    """Memuat konfigurasi dari file JSON."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    default_config = {"base_project_path": "F:/blender"}
    if not os.path.exists(config_path):
        return default_config
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except:
        return default_config

def save_config(config):
    """Menyimpan konfigurasi ke file JSON."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"\n[!] Failed to save configuration: {e}")
        input("Press Enter...")

def tools_settings_menu():
    """Menu untuk mengatur preferensi tools."""
    while True:
        config = load_config()
        clear_screen()
        print("=== TOOLS SETTINGS ===")
        print(f"1. Change Base Project Path (Current: {config['base_project_path']})")
        print("0. Back")
        
        choice = input("\nSelect menu: ")
        if choice == '1':
            new_path = input("\nEnter new project folder path: ").strip()
            if os.path.isdir(new_path):
                config['base_project_path'] = os.path.abspath(new_path)
                save_config(config)
                print("[+] Path updated successfully!")
            else:
                print("[!] Invalid path or folder not found.")
            input("Press Enter...")
        elif choice == '0':
            break

def main_menu():
    while True:
        config = load_config()
        base_project_path = config['base_project_path']

        clear_screen()
        print("=== BLENDER TOOLS MENU ===")
        print("1. Render .blend File")
        print("2. Tools Settings")
        print("0. Exit")
        
        choice = input("\nSelect menu: ")
        
        if choice == '1':
            selected_file = file_browser(base_project_path)
            if selected_file:
                render_settings_menu(selected_file)
        elif choice == '2':
            tools_settings_menu()
        elif choice == '0':
            print("Exiting program...")
            break
        else:
            print("\nChoice not available.")
            input("Press Enter...")

if __name__ == "__main__":
    main_menu()
