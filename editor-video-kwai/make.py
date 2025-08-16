import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageTk
import subprocess
import tempfile
import random
import threading
from pathlib import Path
import json
import re
from tqdm import tqdm
import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    messagebox.showwarning("Aviso", "google-generativeai não instalado. Função de IA desabilitada.")

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    messagebox.showwarning("Aviso", "speech_recognition ou pydub não instalados. Transcrição desabilitada.")

class SimpleVideoEditor:
    def __init__(self):
        self.output_size = (720, 1280)
        self.background_color = (240, 240, 240)
        
    def create_background_image(self, background_path=None, pattern="popcorn"):
        if background_path and os.path.exists(background_path):
            bg = Image.open(background_path)
            bg = bg.resize(self.output_size, Image.Resampling.LANCZOS)
        else:
            bg = Image.new('RGB', self.output_size, self.background_color)
            if pattern == "popcorn":
                self._add_popcorn_pattern(bg)
            elif pattern == "cinema":
                self._add_cinema_pattern(bg)
        return bg
    
    def _add_popcorn_pattern(self, img):
        draw = ImageDraw.Draw(img)
        width, height = img.size
        for i in range(0, width, 100):
            for j in range(0, height, 120):
                x = i + np.random.randint(-30, 30)
                y = j + np.random.randint(-30, 30)
                self._draw_popcorn_bucket(draw, x, y)
    
    def _draw_popcorn_bucket(self, draw, x, y):
        bucket_points = [
            (x, y + 40), (x + 50, y + 40),
            (x + 45, y + 10), (x + 5, y + 10)
        ]
        draw.polygon(bucket_points, fill=(220, 20, 20), outline=(180, 0, 0))
        for i in range(3):
            y_stripe = y + 15 + i * 8
            draw.line([(x + 5, y_stripe), (x + 45, y_stripe)], fill=(255, 255, 255), width=2)
        for i in range(4):
            px = x + 10 + i * 8 + np.random.randint(-3, 3)
            py = y - 5 + np.random.randint(-8, 5)
            draw.ellipse([px, py, px + 6, py + 6], fill=(255, 215, 0))
    
    def _add_cinema_pattern(self, img):
        draw = ImageDraw.Draw(img)
        width, height = img.size
        for i in range(0, width, 80):
            for j in range(0, height, 100):
                x = i + np.random.randint(-20, 20)
                y = j + np.random.randint(-20, 20)
                draw.ellipse([x, y, x + 30, y + 30], fill=(50, 50, 50))
                draw.ellipse([x + 5, y + 5, x + 25, y + 25], fill=(200, 200, 200))
    
    def apply_subtle_anti_plagiarism_effects(self, frame, frame_number, total_frames):
        progress = frame_number / total_frames
        video_seed = hash(str(total_frames)) % 100
        brightness_factor = 1.0 + (video_seed % 10 - 5) * 0.02
        contrast_factor = 1.0 + (video_seed % 8 - 4) * 0.015
        frame = cv2.convertScaleAbs(frame, alpha=contrast_factor, beta=brightness_factor * 5)
        if video_seed % 3 == 0:
            h, w = frame.shape[:2]
            crop_size = 1
            frame = frame[crop_size:h-crop_size, crop_size:w-crop_size]
        return frame
    
    def check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def extract_audio(self, video_path, temp_audio_path):
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '1',
                temp_audio_path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception:
            return False
    
    def transcribe_audio(self, audio_path):
        if not SPEECH_AVAILABLE:
            return ""
        
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio, language="pt-BR")
            return transcription
        except Exception:
            return ""
    
    def extract_context_from_scene(self, video_path, api_key):
        fallback_titles = [
            "Nada podia deter aquilo.",
            "Isso não podia ter acontecido...",
            "O que aconteceu vai te chocar.",
            "Quando tudo parecia normal...",
            "Você vai se arrepiar com isso.",
            "Era para ser só mais um dia...",
            "O erro que mudou tudo.",
            "Isso saiu do controle.",
            "Ninguém percebeu o que viria.",
            "Uma decisão. Um destino."
        ]

        def gerar_prompt(com_base):
            return f"""
            Crie um título curto e impactante (máximo de 40 caracteres) para um corte de cena de filme, destinado a redes sociais como o Kwai.

            O título deve:
            - Ser direto, chamativo e fácil de entender;
            - Despertar curiosidade, tensão ou emoção;
            - Refletir fielmente o conteúdo da cena, com base no conteúdo abaixo;
            - Ser compatível com o estilo de vídeos virais curtos;
            - Não conter emojis, hashtags ou explicações.

            Contexto: "{com_base}"

            Retorne apenas o título e caso esteja em outro idioma, traduzir para o português br.
            """

        def limpar_nome_arquivo(path):
            nome = os.path.basename(path)
            nome = os.path.splitext(nome)[0]
            nome = nome.replace('_', ' ').replace('-', ' ')
            nome = re.sub(r'\d+', '', nome)
            nome = nome.strip()
            if len(nome.split()) >= 2 and not nome.lower().startswith("video"):
                return nome.capitalize()
            return None

        if not GEMINI_AVAILABLE or not api_key:
            return random.choice(fallback_titles)

        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio_path = temp_audio.name
        temp_audio.close()

        try:
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            
            if not self.extract_audio(video_path, temp_audio_path):
                context = limpar_nome_arquivo(video_path)
                if context:
                    prompt = gerar_prompt(context)
                    response = gemini_model.generate_content(prompt)
                    title = response.text.strip()
                    if title and len(title) <= 40:
                        return title
                return random.choice(fallback_titles)

            transcription = self.transcribe_audio(temp_audio_path)
            if not transcription:
                context = limpar_nome_arquivo(video_path)
                if context:
                    prompt = gerar_prompt(context)
                    response = gemini_model.generate_content(prompt)
                    title = response.text.strip()
                    if title and len(title) <= 40:
                        return title
                return random.choice(fallback_titles)

            prompt = gerar_prompt(transcription)
            response = gemini_model.generate_content(prompt)
            title = response.text.strip()

            if title and len(title) <= 40:
                return title
            else:
                context = limpar_nome_arquivo(video_path)
                if context:
                    prompt = gerar_prompt(context)
                    response = gemini_model.generate_content(prompt)
                    title = response.text.strip()
                    if title and len(title) <= 40:
                        return title
                return random.choice(fallback_titles)

        except Exception:
            return random.choice(fallback_titles)
        finally:
            try:
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
            except:
                pass
    
    def add_text_to_image(self, img, text, position='top', font_size=50):
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size

        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()

        text = text.upper()
        max_line_width_for_wrap = img_width - 80

        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        processed_lines = []
        for line in text.split('\n'):
            words = line.split()
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                width = temp_draw.textbbox((0, 0), test_line, font=font)[2]
                if width <= max_line_width_for_wrap:
                    current_line = test_line
                else:
                    if current_line:
                        processed_lines.append(current_line)
                    current_line = word
            if current_line:
                processed_lines.append(current_line)

        if not processed_lines:
            processed_lines = [""]

        line_height = font.getmetrics()[0] + font.getmetrics()[1]
        total_text_height = len(processed_lines) * (line_height + 10) - 10

        if position == 'top':
            start_y = 100
        else:
            start_y = (img_height - total_text_height) // 2 + 50

        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        y = start_y
        for line in processed_lines:
            line_width = temp_draw.textbbox((0, 0), line, font=font)[2]
            x = (img_width - line_width) // 2

            draw_overlay.text(
                (x, y),
                line,
                font=font,
                fill=(255, 214, 0),
                stroke_width=2,
                stroke_fill=(0, 0, 0)
            )
            y += line_height + 10

        img.paste(overlay, (0, 0), overlay)
        return img

    def process_video_with_opencv(self, input_path, output_path, background_image=None, 
                                 custom_title=None, title_position='top', anti_plagiarism=True,
                                 api_key=None, progress_callback=None, stop_event=None):
        has_ffmpeg = self.check_ffmpeg()
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video_path = temp_video.name
        temp_video.close()
        
        try:
            success = self._process_video_frames(
                input_path, temp_video_path, background_image, 
                custom_title, title_position, anti_plagiarism, api_key, 
                progress_callback, stop_event
            )
            if not success:
                return False
            
            if has_ffmpeg and not stop_event.is_set():
                self._add_audio_with_ffmpeg(input_path, temp_video_path, output_path)
            else:
                import shutil
                shutil.move(temp_video_path, output_path)
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"Erro: {e}")
            return False
        finally:
            try:
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
            except:
                pass
        
    def _add_audio_with_ffmpeg(self, original_video, processed_video, output_path):
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', processed_video,
                '-i', original_video,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-vsync', '0',
                '-async', '1',
                '-strict', '-2',
                output_path
            ]
            subprocess.run(cmd, capture_output=True, text=True)
        except Exception:
            import shutil
            shutil.copy2(processed_video, output_path)

    def _process_video_frames(self, input_path, output_path, background_image=None, 
                             custom_title=None, title_position='top', anti_plagiarism=True,
                             api_key=None, progress_callback=None, stop_event=None):
        
        cap = cv2.VideoCapture(input_path)
        
        if not cap.isOpened():
            if progress_callback:
                progress_callback(f"Erro: Não foi possível abrir o vídeo {input_path}")
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        background = self.create_background_image(background_image)
        
        if custom_title:
            title_text = custom_title
        else:
            title_text = self.extract_context_from_scene(input_path, api_key)
        
        if progress_callback:
            progress_callback(f"Título: {title_text}")
        
        background_with_title = self.add_text_to_image(
            background.copy(), 
            title_text, 
            title_position,
            font_size=50
        )
        
        bg_cv = cv2.cvtColor(np.array(background_with_title), cv2.COLOR_RGB2BGR)
        
        video_area_top = 350
        video_area_bottom = 400
        video_area_height = self.output_size[1] - video_area_top - video_area_bottom
        video_area_width = self.output_size[0]

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, self.output_size)
        
        frame_count = 0
        for frame_idx in range(total_frames):
            if stop_event and stop_event.is_set():
                if progress_callback:
                    progress_callback("Processamento interrompido pelo usuário.")
                cap.release()
                out.release()
                return False
            
            ret, frame = cap.read()
            if not ret:
                break
            
            if anti_plagiarism:
                frame = self.apply_subtle_anti_plagiarism_effects(frame, frame_idx, total_frames)
            
            original_height, original_width = frame.shape[:2]
            
            scale_width = video_area_width / original_width
            scale_height = video_area_height / original_height
            scale = max(scale_width, scale_height)
            
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            frame_resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            if new_width > video_area_width:
                crop_x = (new_width - video_area_width) // 2
                frame_resized = frame_resized[:, crop_x:crop_x + video_area_width]
                new_width = video_area_width
                
            if new_height > video_area_height:
                crop_y = (new_height - video_area_height) // 2
                frame_resized = frame_resized[crop_y:crop_y + video_area_height, :]
                new_height = video_area_height
            
            final_frame = bg_cv.copy()
            
            x_offset = (video_area_width - new_width) // 2
            y_offset = video_area_top + (video_area_height - new_height) // 2
            
            final_y_end = min(y_offset + new_height, video_area_top + video_area_height)
            final_x_end = min(x_offset + new_width, video_area_width)

            new_height_adjusted = final_y_end - y_offset
            new_width_adjusted = final_x_end - x_offset

            if new_height_adjusted < frame_resized.shape[0] or new_width_adjusted < frame_resized.shape[1]:
                frame_resized = frame_resized[:new_height_adjusted, :new_width_adjusted]

            final_frame[y_offset:final_y_end, x_offset:final_x_end] = frame_resized
            
            font_cv = cv2.FONT_HERSHEY_SIMPLEX
            font_scale_cv = 2.0
            thickness_cv = 3
            text_watermark = "@impactofinal"
            text_size_cv = cv2.getTextSize(text_watermark, font_cv, font_scale_cv, thickness_cv)[0]
            text_x_cv = (self.output_size[0] - text_size_cv[0]) // 2
            text_y_cv = self.output_size[1] - 50
            
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        cv2.putText(final_frame, text_watermark, (text_x_cv + dx, text_y_cv + dy),
                                    font_cv, font_scale_cv, (0, 0, 0), thickness_cv)
            
            cv2.putText(final_frame, text_watermark, (text_x_cv, text_y_cv),
                        font_cv, font_scale_cv, (0, 255, 255), thickness_cv)
            
            out.write(final_frame)
            frame_count += 1
            
            if progress_callback and frame_idx % 10 == 0:
                progress = (frame_idx / total_frames) * 100
                progress_callback(f"Processando: {progress:.1f}%")
        
        cap.release()
        out.release()
        
        return True

class VideoEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kwai Video Editor")
        
        # Responsive window size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(850, int(screen_width * 0.85))
        window_height = min(650, int(screen_height * 0.85))
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg='#212121')
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.setup_styles()
        
        self.api_key = tk.StringVar()
        self.input_dir = tk.StringVar(value="videos_originais")
        self.output_dir = tk.StringVar(value="videos_editados")
        self.background_dir = tk.StringVar(value="backgrounds")
        self.custom_title = tk.StringVar()
        self.title_position = tk.StringVar(value="top")
        self.anti_plagiarism = tk.BooleanVar(value=True)
        self.shutdown_after = tk.BooleanVar(value=False)
        self.stop_event = threading.Event()
        self.processing_thread = None
        
        self.editor = SimpleVideoEditor()
        
        self.load_config()
        
        self.create_widgets()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', 
                       background='#212121', 
                       foreground='#ffffff', 
                       font=('Segoe UI', 20, 'bold'),
                       padding=12)
        
        style.configure('Heading.TLabel', 
                       background='#212121', 
                       foreground='#bbdefb', 
                       font=('Segoe UI', 12, 'bold'),
                       padding=6)
        
        style.configure('Normal.TLabel', 
                       background='#212121', 
                       foreground='#e0e0e0', 
                       font=('Segoe UI', 10))
        
        style.configure('Custom.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       background='#424242',
                       foreground='#ffffff',
                       padding=8,
                       borderwidth=0)
        style.map('Custom.TButton',
                 background=[('active', '#616161'), ('disabled', '#757575')],
                 foreground=[('active', '#ffffff'), ('disabled', '#a0a0a0')])
        
        style.configure('Process.TButton',
                       font=('Segoe UI', 12, 'bold'),
                       background='#0288d1',
                       foreground='#ffffff',
                       padding=10,
                       borderwidth=0)
        style.map('Process.TButton',
                 background=[('active', '#039be5'), ('disabled', '#90caf9')],
                 foreground=[('active', '#ffffff'), ('disabled', '#a0a0a0')])
        
        style.configure('TEntry',
                       fieldbackground='#303030',
                       foreground='#ffffff',
                       insertcolor='#ffffff',
                       padding=6)
        
        style.configure('TCheckbutton',
                       background='#212121',
                       foreground='#e0e0e0',
                       font=('Segoe UI', 10))
        
        style.configure('TNotebook',
                       background='#212121',
                       tabmargins=0)
        style.configure('TNotebook.Tab',
                       background='#424242',
                       foreground='#e0e0e0',
                       padding=[10, 5],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', '#0288d1'), ('active', '#616161')],
                 foreground=[('selected', '#ffffff'), ('active', '#ffffff')])
        
        style.configure('TProgressbar',
                       background='#0288d1',
                       troughcolor='#303030',
                       borderwidth=0)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, 
                               text="Kwai Video Editor", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        
        notebook = ttk.Notebook(main_frame, style='TNotebook')
        notebook.grid(row=1, column=0, sticky="nsew")
        
        config_frame = ttk.Frame(notebook, padding=10)
        notebook.add(config_frame, text="Configurações")
        self.create_config_tab(config_frame)
        
        process_frame = ttk.Frame(notebook, padding=10)
        notebook.add(process_frame, text="Processar")
        self.create_process_tab(process_frame)
        
        log_frame = ttk.Frame(notebook, padding=10)
        notebook.add(log_frame, text="Log")
        self.create_log_tab(log_frame)
    
    def create_config_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        
        api_frame = ttk.LabelFrame(parent, text="API Configuration", padding=10)
        api_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        api_frame.columnconfigure(0, weight=1)
        
        ttk.Label(api_frame, text="Google API Key (Gemini):", style='Normal.TLabel').grid(row=0, column=0, sticky="w")
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=35, show="*")
        api_entry.grid(row=1, column=0, sticky="ew", pady=(5, 5))
        ttk.Label(api_frame, 
                 text="Get your key at: makersuite.google.com/app/apikey", 
                 style='Normal.TLabel', 
                 foreground='#90a4ae').grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        dirs_frame = ttk.LabelFrame(parent, text="Directories", padding=10)
        dirs_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        dirs_frame.columnconfigure(0, weight=1)
        
        ttk.Label(dirs_frame, text="Input Videos Folder:", style='Normal.TLabel').grid(row=0, column=0, sticky="w")
        input_frame = ttk.Frame(dirs_frame)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(5, 5))
        input_frame.columnconfigure(0, weight=1)
        ttk.Entry(input_frame, textvariable=self.input_dir).grid(row=0, column=0, sticky="ew")
        ttk.Button(input_frame, text="Browse", command=self.browse_input_dir, style='Custom.TButton').grid(row=0, column=1, padx=(5, 0))
        
        ttk.Label(dirs_frame, text="Output Videos Folder:", style='Normal.TLabel').grid(row=2, column=0, sticky="w")
        output_frame = ttk.Frame(dirs_frame)
        output_frame.grid(row=3, column=0, sticky="ew", pady=(5, 5))
        output_frame.columnconfigure(0, weight=1)
        ttk.Entry(output_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky="ew")
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir, style='Custom.TButton').grid(row=0, column=1, padx=(5, 0))
        
        ttk.Label(dirs_frame, text="Backgrounds Folder (Optional):", style='Normal.TLabel').grid(row=4, column=0, sticky="w")
        bg_frame = ttk.Frame(dirs_frame)
        bg_frame.grid(row=5, column=0, sticky="ew", pady=(5, 5))
        bg_frame.columnconfigure(0, weight=1)
        ttk.Entry(bg_frame, textvariable=self.background_dir).grid(row=0, column=0, sticky="ew")
        ttk.Button(bg_frame, text="Browse", command=self.browse_background_dir, style='Custom.TButton').grid(row=0, column=1, padx=(5, 0))
        
        options_frame = ttk.LabelFrame(parent, text="Options", padding=10)
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        options_frame.columnconfigure(0, weight=1)
        
        ttk.Label(options_frame, text="Custom Title (Leave empty for AI):", style='Normal.TLabel').grid(row=0, column=0, sticky="w")
        ttk.Entry(options_frame, textvariable=self.custom_title).grid(row=1, column=0, sticky="ew", pady=(5, 5))
        
        pos_frame = ttk.Frame(options_frame)
        pos_frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(pos_frame, text="Title Position:", style='Normal.TLabel').pack(side=tk.LEFT)
        ttk.Radiobutton(pos_frame, text="Top", variable=self.title_position, value="top").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(pos_frame, text="Bottom", variable=self.title_position, value="bottom").pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Checkbutton(options_frame, text="Apply Anti-Plagiarism Effects", 
                       variable=self.anti_plagiarism).grid(row=3, column=0, sticky="w", pady=(5, 5))
        ttk.Checkbutton(options_frame, text="Shutdown After Processing", 
                       variable=self.shutdown_after).grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        ttk.Button(parent, text="Save Configuration", 
                  command=self.save_config, style='Custom.TButton').grid(row=3, column=0, pady=10, sticky="e")
    
    def create_process_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready to process", style='Normal.TLabel')
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, style='TProgressbar')
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        self.process_button = ttk.Button(buttons_frame, 
                                        text="Process Videos", 
                                        command=self.start_processing, 
                                        style='Process.TButton')
        self.process_button.grid(row=0, column=0, sticky="e", padx=(0, 5))
        
        self.stop_button = ttk.Button(buttons_frame, 
                                     text="Stop", 
                                     command=self.stop_processing,
                                     state=tk.DISABLED,
                                     style='Custom.TButton')
        self.stop_button.grid(row=0, column=1, sticky="w", padx=(5, 0))
        
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding=10)
        preview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_label = ttk.Label(preview_frame, text="No preview available", style='Normal.TLabel')
        self.preview_label.pack(expand=True, fill=tk.BOTH)
    
    def create_log_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        log_frame = ttk.LabelFrame(parent, text="Processing Log", padding=10)
        log_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=12,
                                                 bg='#303030',
                                                 fg='#e0e0e0',
                                                 font=('Consolas', 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        ttk.Button(parent, text="Clear Log", command=self.clear_log, 
                  style='Custom.TButton').grid(row=1, column=0, pady=10, sticky="e")
    
    def browse_input_dir(self):
        directory = filedialog.askdirectory(title="Select Input Videos Folder")
        if directory:
            self.input_dir.set(directory)
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Videos Folder")
        if directory:
            self.output_dir.set(directory)
    
    def browse_background_dir(self):
        directory = filedialog.askdirectory(title="Select Backgrounds Folder")
        if directory:
            self.background_dir.set(directory)
    
    def log_message(self, message):
        self.log_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.log_message(message)
    
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def save_config(self):
        config = {
            'api_key': self.api_key.get(),
            'input_dir': self.input_dir.get(),
            'output_dir': self.output_dir.get(),
            'background_dir': self.background_dir.get(),
            'custom_title': self.custom_title.get(),
            'title_position': self.title_position.get(),
            'anti_plagiarism': self.anti_plagiarism.get(),
            'shutdown_after': self.shutdown_after.get()
        }
        
        try:
            with open('video_editor_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        try:
            if os.path.exists('video_editor_config.json'):
                with open('video_editor_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.api_key.set(config.get('api_key', ''))
                self.input_dir.set(config.get('input_dir', 'videos_originais'))
                self.output_dir.set(config.get('output_dir', 'videos_editados'))
                self.background_dir.set(config.get('background_dir', 'backgrounds'))
                self.custom_title.set(config.get('custom_title', ''))
                self.title_position.set(config.get('title_position', 'top'))
                self.anti_plagiarism.set(config.get('anti_plagiarism', True))
                self.shutdown_after.set(config.get('shutdown_after', False))
        except Exception as e:
            self.log_message(f"Failed to load configuration: {e}")
    
    def start_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showwarning("Warning", "Processing is already running. Please stop it first.")
            return
        
        if not os.path.exists(self.input_dir.get()):
            messagebox.showerror("Error", f"Input folder does not exist: {self.input_dir.get()}")
            return
        
        if not self.api_key.get() and GEMINI_AVAILABLE:
            if not messagebox.askyesno("Warning", 
                                     "API Key not configured. Continue with random titles?"):
                return
        
        os.makedirs(self.output_dir.get(), exist_ok=True)
        
        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.stop_event.clear()
        
        self.processing_thread = threading.Thread(target=self.process_videos)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop_processing(self):
        self.stop_event.set()
        self.update_status("Stopping processing... Please wait.")
        # Schedule a check to ensure thread termination
        self.root.after(100, self.check_thread_termination)
    
    def check_thread_termination(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.root.after(100, self.check_thread_termination)
        else:
            self.update_status("Processing stopped.")
            self.process_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_progress(0)
            self.processing_thread = None
    
    def process_videos(self):
        try:
            input_path = Path(self.input_dir.get())
            video_extensions = ('.mp4', '.avi', '.mkv', '.webm', '.mov')
            video_files = [f for f in input_path.glob('*') if f.suffix.lower() in video_extensions]
            
            if not video_files:
                self.update_status("No videos found in input folder.")
                return
            
            self.update_status(f"Found {len(video_files)} videos to process.")
            
            background_files = []
            if os.path.exists(self.background_dir.get()):
                background_files = [os.path.join(self.background_dir.get(), f) 
                                  for f in os.listdir(self.background_dir.get())
                                  if f.lower().endswith(('.png', '.jpeg', '.jpg'))]
            
            if not background_files:
                self.update_status("No backgrounds found. Using default.")
            
            for i, video_file in enumerate(video_files):
                if self.stop_event.is_set():
                    self.update_status("Processing stopped by user.")
                    break
                
                self.update_status(f"Processing {video_file.name}...")
                
                output_name = f"{video_file.stem}_editado.mp4"
                output_path = os.path.join(self.output_dir.get(), output_name)
                
                background_path = random.choice(background_files) if background_files else None
                
                def progress_callback(message):
                    if not self.stop_event.is_set():
                        self.update_status(message)
                
                try:
                    success = self.editor.process_video_with_opencv(
                        input_path=str(video_file),
                        output_path=output_path,
                        background_image=background_path,
                        custom_title=self.custom_title.get() if self.custom_title.get() else None,
                        title_position=self.title_position.get(),
                        anti_plagiarism=self.anti_plagiarism.get(),
                        api_key=self.api_key.get(),
                        progress_callback=progress_callback,
                        stop_event=self.stop_event
                    )
                    
                    if self.stop_event.is_set():
                        self.update_status(f"Processing of {video_file.name} interrupted.")
                        break
                        
                    if success:
                        self.update_status(f"✅ {video_file.name} processed successfully!")
                    else:
                        self.update_status(f"❌ Error processing {video_file.name}")
                        
                except Exception as e:
                    self.update_status(f"❌ Error processing {video_file.name}: {e}")
                
                progress = ((i + 1) / len(video_files)) * 100
                self.update_progress(progress)
            
            if not self.stop_event.is_set():
                self.update_status(f"🎉 Processing complete! {len(video_files)} videos processed.")
            
            if self.shutdown_after.get() and not self.stop_event.is_set():
                self.update_status("Shutting down in 30 seconds...")
                if os.name == 'nt':
                    os.system("shutdown /s /t 30")
                else:
                    os.system("shutdown -h +0.5")
            
        except Exception as e:
            self.update_status(f"❌ General processing error: {e}")
        
        finally:
            self.process_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_progress(0)
            self.stop_event.clear()
            self.processing_thread = None
    
    def on_closing(self):
        self.stop_event.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        self.save_config()
        self.root.destroy()

def main():
    missing_deps = []
    
    if not GEMINI_AVAILABLE:
        missing_deps.append("google-generativeai")
    
    if not SPEECH_AVAILABLE:
        missing_deps.append("speech_recognition e/ou pydub")
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    
    if missing_deps:
        print("⚠️  Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nInstall with: pip install " + " ".join(missing_deps))
        input("Press Enter to continue anyway...")
    
    root = tk.Tk()
    app = VideoEditorGUI(root)
    
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == '__main__':
    main()