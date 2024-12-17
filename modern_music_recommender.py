# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from ttkthemes import ThemedTk
import time
from PIL import Image, ImageTk
import os
from surprise import Dataset, Reader, SVD
from surprise.model_selection import cross_validate
import logging
from colorama import init, Fore, Style
import threading
from tqdm import tqdm
import webbrowser
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from collections import Counter

# 로깅 설정
init()  # colorama 초기화
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - {Fore.GREEN}%(levelname)s{Style.RESET_ALL} - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def create_music_icon():
    if not os.path.exists('assets'):
        os.makedirs('assets')
    icon_path = 'assets/music_icon.ico'
    return icon_path

class ModernStyle:
    COLORS = {
        'bg_dark': '#1E1E1E',
        'bg_light': '#2D2D2D',
        'accent': '#7289DA',
        'text': '#FFFFFF',
        'text_secondary': '#B9BBBE',
        'success': '#43B581',
        'warning': '#FAA61A',
        'error': '#F04747',
        'chart_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
    }
    
    FONTS = {
        'header': ('Helvetica', 18, 'bold'),
        'subheader': ('Helvetica', 14, 'bold'),
        'normal': ('Helvetica', 10),
        'small': ('Helvetica', 9)
    }

class MusicRecommender:
    def __init__(self):
        self.style = ModernStyle()
        self.setup_data()
        self.setup_gui()
        self.load_rating_history()
        self.svd_model = None
        self.show_welcome_message()
        
    def setup_data(self):
        logging.info("음악 데이터베이스 초기화 중...")
        
        # 장르별 음악 데이터
        self.music_data = {
            "K-POP": [
                {"title": "Dynamite", "artist": "BTS", "genre": "K-POP"},
                {"title": "How You Like That", "artist": "BLACKPINK", "genre": "K-POP"},
                {"title": "Ditto", "artist": "NewJeans", "genre": "K-POP"},
                {"title": "Love Dive", "artist": "IVE", "genre": "K-POP"},
                {"title": "After LIKE", "artist": "IVE", "genre": "K-POP"}
            ],
            "POP": [
                {"title": "Shape of You", "artist": "Ed Sheeran", "genre": "POP"},
                {"title": "Anti-Hero", "artist": "Taylor Swift", "genre": "POP"},
                {"title": "Starboy", "artist": "The Weeknd", "genre": "POP"},
                {"title": "As It Was", "artist": "Harry Styles", "genre": "POP"},
                {"title": "Blinding Lights", "artist": "The Weeknd", "genre": "POP"}
            ],
            "Rock": [
                {"title": "Believer", "artist": "Imagine Dragons", "genre": "Rock"},
                {"title": "Bohemian Rhapsody", "artist": "Queen", "genre": "Rock"},
                {"title": "Do I Wanna Know?", "artist": "Arctic Monkeys", "genre": "Rock"},
                {"title": "Thunder", "artist": "Imagine Dragons", "genre": "Rock"},
                {"title": "We Will Rock You", "artist": "Queen", "genre": "Rock"}
            ],
            "Hip-Hop": [
                {"title": "God's Plan", "artist": "Drake", "genre": "Hip-Hop"},
                {"title": "HUMBLE.", "artist": "Kendrick Lamar", "genre": "Hip-Hop"},
                {"title": "SICKO MODE", "artist": "Travis Scott", "genre": "Hip-Hop"},
                {"title": "Hotline Bling", "artist": "Drake", "genre": "Hip-Hop"},
                {"title": "goosebumps", "artist": "Travis Scott", "genre": "Hip-Hop"}
            ],
            "R&B": [
                {"title": "Kill Bill", "artist": "SZA", "genre": "R&B"},
                {"title": "Pink + White", "artist": "Frank Ocean", "genre": "R&B"},
                {"title": "Best Part", "artist": "Daniel Caesar", "genre": "R&B"},
                {"title": "Good Days", "artist": "SZA", "genre": "R&B"},
                {"title": "Get You", "artist": "Daniel Caesar", "genre": "R&B"}
            ]
        }
        
        # 사용자 데이터 초기화
        self.ratings = pd.DataFrame(columns=['user_id', 'song_id', 'rating', 'timestamp'])
        self.current_user_id = 1
        
        # 곡 ID 매핑 생성
        self.song_id_mapping = {}
        song_id = 0
        for genre in self.music_data:
            for song in self.music_data[genre]:
                song_key = f"{song['title']} - {song['artist']}"
                self.song_id_mapping[song_key] = song_id
                song_id += 1
        
        logging.info(f"{Fore.GREEN}데이터베이스 초기화 완료{Style.RESET_ALL}")
        
    def setup_gui(self):
        logging.info("GUI 초기화 중...")
        
        # 메인 윈도우 설정
        self.root = ThemedTk(theme="equilux")
        self.root.title("Music Recommender Pro")
        self.root.geometry("800x600")
        
        # 아이콘 설정
        try:
            icon_path = create_music_icon()
            if os.path.exists(icon_path):
                # Windows에서는 .ico 파일 사용
                if os.name == 'nt':
                    self.root.iconbitmap(default=icon_path)
                # Linux/Mac에서는 .png 파일 사용
                else:
                    icon_img = tk.PhotoImage(file='assets/music_icon.png')
                    self.root.iconphoto(True, icon_img)
                logging.info(f"{Fore.GREEN}아이콘 설정 완료{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"아이콘 설정 중 오류 발생: {str(e)}")
        
        # 스타일 설정
        style = ttk.Style()
        style.configure("Custom.TFrame", background="#2E2E2E")
        style.configure("Custom.TLabel", background="#2E2E2E", foreground="white")
        style.configure("Custom.TButton", padding=10)
        
        # 메인 프레임
        self.main_frame = ttk.Frame(self.root, style="Custom.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 탭 컨트롤
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # 평가 탭
        self.rating_tab = ttk.Frame(self.tab_control)
        self.setup_rating_tab()
        
        # 추천 탭
        self.recommendation_tab = ttk.Frame(self.tab_control)
        self.setup_recommendation_tab()
        
        # 히스토리 탭
        self.history_tab = ttk.Frame(self.tab_control)
        self.setup_history_tab()
        
        # 통계 탭
        self.stats_tab = ttk.Frame(self.tab_control)
        self.setup_stats_tab()
        
        # 새로운 탭 추가
        self.playlist_tab = ttk.Frame(self.tab_control)
        self.trends_tab = ttk.Frame(self.tab_control)
        self.setup_playlist_tab()
        self.setup_trends_tab()
        
        self.tab_control.add(self.rating_tab, text="음악 평가")
        self.tab_control.add(self.recommendation_tab, text="추천")
        self.tab_control.add(self.history_tab, text="히스토리")
        self.tab_control.add(self.stats_tab, text="통계")
        self.tab_control.add(self.playlist_tab, text="🎼 플레이리스트")
        self.tab_control.add(self.trends_tab, text="📈 트렌드")
        self.tab_control.pack(expand=True, fill="both")
        
        logging.info(f"{Fore.GREEN}GUI 초기화 완료{Style.RESET_ALL}")
        
    def setup_rating_tab(self):
        # 장르 선택
        ttk.Label(self.rating_tab, text="장르 선택:").pack(pady=10)
        self.genre_var = tk.StringVar()
        genre_combo = ttk.Combobox(self.rating_tab, textvariable=self.genre_var, values=list(self.music_data.keys()))
        genre_combo.pack(pady=5)
        genre_combo.bind('<<ComboboxSelected>>', self.update_songs)
        
        # 곡 선택
        ttk.Label(self.rating_tab, text="곡 선택:").pack(pady=10)
        self.song_var = tk.StringVar()
        self.song_combo = ttk.Combobox(self.rating_tab, textvariable=self.song_var)
        self.song_combo.pack(pady=5)
        
        # 평점 입력
        ttk.Label(self.rating_tab, text="평점 (1-5):").pack(pady=10)
        self.rating_scale = ttk.Scale(self.rating_tab, from_=1, to=5, orient="horizontal")
        self.rating_scale.pack(pady=5)
        
        # 제출 버튼
        submit_btn = ttk.Button(self.rating_tab, text="평가 제출", command=self.submit_rating)
        submit_btn.pack(pady=20)
        
    def setup_recommendation_tab(self):
        # 추테이너 프레임
        container = ttk.Frame(self.recommendation_tab, style="Custom.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 추천 설정 프레임
        settings_frame = ttk.LabelFrame(container, text="추천 설정", style="Custom.TFrame")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 추천 방식 선택
        method_frame = ttk.Frame(settings_frame, style="Custom.TFrame")
        method_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(method_frame, text="추천 방식:", style="Custom.TLabel").pack(side=tk.LEFT)
        self.rec_method_var = tk.StringVar()
        rec_method_combo = ttk.Combobox(
            method_frame,
            textvariable=self.rec_method_var,
            values=["협업 필터링", "장르 기반", "아티스트 기반", "하이브리드"],
            width=20
        )
        rec_method_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 추천 곡 수 설정
        count_frame = ttk.Frame(settings_frame, style="Custom.TFrame")
        count_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(count_frame, text="추천 곡 수:", style="Custom.TLabel").pack(side=tk.LEFT)
        self.rec_count_var = tk.StringVar(value="5")
        rec_count_combo = ttk.Combobox(
            count_frame,
            textvariable=self.rec_count_var,
            values=["3", "5", "10", "15", "20"],
            width=5
        )
        rec_count_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 최소 평점 필터
        filter_frame = ttk.Frame(settings_frame, style="Custom.TFrame")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="최소 평점:", style="Custom.TLabel").pack(side=tk.LEFT)
        self.min_rating_var = tk.StringVar(value="3")
        min_rating_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.min_rating_var,
            values=["1", "2", "3", "4", "5"],
            width=5
        )
        min_rating_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 추천 받기 버튼
        btn_frame = ttk.Frame(container, style="Custom.TFrame")
        btn_frame.pack(fill=tk.X, pady=10)
        
        rec_btn = ttk.Button(
            btn_frame,
            text="추천 받기",
            command=self.get_recommendations,
            style="Custom.TButton"
        )
        rec_btn.pack(expand=True)
        
        # 결과 표시 영역
        result_frame = ttk.LabelFrame(container, text="추천 결과", style="Custom.TFrame")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.rec_result = tk.Text(
            result_frame,
            wrap=tk.WORD,
            height=15,
            width=50,
            bg="#2E2E2E",
            fg="white",
            font=("Helvetica", 10)
        )
        self.rec_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_history_tab(self):
        # 히스토리 표시
        self.history_text = tk.Text(self.history_tab, height=20, width=50)
        self.history_text.pack(pady=10)
        
        # 새로고침 버튼
        refresh_btn = ttk.Button(self.history_tab, text="새로고침", command=self.refresh_history)
        refresh_btn.pack(pady=10)
        
    def setup_stats_tab(self):
        # 통계 정보 표시
        self.stats_text = tk.Text(self.stats_tab, height=20, width=50)
        self.stats_text.pack(pady=10)
        
        # 통계 업데이트 버튼
        update_stats_btn = ttk.Button(self.stats_tab, text="통계 업데이트", command=self.update_stats)
        update_stats_btn.pack(pady=10)
        
    def setup_playlist_tab(self):
        container = ttk.Frame(self.playlist_tab, style="Custom.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 플레이리스트 목록
        list_frame = ttk.LabelFrame(container, text="내 플레이리스트", style="Custom.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.playlist_listbox = tk.Listbox(
            list_frame,
            bg=self.style.COLORS['bg_light'],
            fg=self.style.COLORS['text'],
            selectmode=tk.SINGLE,
            font=self.style.FONTS['normal'],
            yscrollcommand=scrollbar.set
        )
        self.playlist_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=self.playlist_listbox.yview)
        
        # 기존 플레이리스트 로드
        self.load_playlists()
        
        # 컨트롤 프레임
        control_frame = ttk.Frame(container, style="Custom.TFrame")
        control_frame.pack(fill=tk.X, pady=5)
        
        # 버튼들
        ttk.Button(
            control_frame,
            text="새 플레이리스트",
            command=self.create_playlist,
            style="Custom.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="곡 추가",
            command=self.add_to_playlist,
            style="Custom.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="플레이리스트 공유",
            command=self.share_playlist,
            style="Custom.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # 삭제 버튼 추가
        ttk.Button(
            control_frame,
            text="삭제",
            command=self.delete_playlist,
            style="Custom.TButton"
        ).pack(side=tk.LEFT, padx=5)

    def setup_trends_tab(self):
        container = ttk.Frame(self.trends_tab, style="Custom.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 차트 프레임
        chart_frame = ttk.LabelFrame(container, text="트렌드 분석", style="Custom.TFrame")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 차트 캔버스
        self.fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        self.fig.patch.set_facecolor(self.style.COLORS['bg_dark'])
        
        canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 업데이트 버튼
        ttk.Button(
            container,
            text="트렌드 업데이트",
            command=self.update_trends,
            style="Custom.TButton"
        ).pack(pady=10)

    def update_songs(self, event=None):
        genre = self.genre_var.get()
        if genre in self.music_data:
            songs = [f"{song['title']} - {song['artist']}" for song in self.music_data[genre]]
            self.song_combo['values'] = songs
            
    def submit_rating(self):
        genre = self.genre_var.get()
        song_info = self.song_var.get()
        rating = self.rating_scale.get()
        
        if not genre or not song_info:
            messagebox.showerror("오류", "장르와 곡을 선택해주세요.")
            return
            
        try:
            # 평가 데이터 추가
            song_id = self.song_id_mapping.get(song_info, len(self.ratings))
            timestamp = datetime.now().timestamp()
            
            new_rating = pd.DataFrame({
                'user_id': [self.current_user_id],
                'song_id': [song_id],
                'rating': [rating],
                'timestamp': [timestamp]
            })
            
            self.ratings = pd.concat([self.ratings, new_rating], ignore_index=True)
            
            # 평가 히스토리 저장
            self.save_rating_history(genre, song_info, rating)
            
            messagebox.showinfo("성공", "평가가 저장되었습니다!")
            logging.info(f"{Fore.GREEN}새로운 평가 저장됨: {song_info} - {rating}점{Style.RESET_ALL}")
            
        except Exception as e:
            logging.error(f"평가 저장 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", "평가 저장 중 문제가 발생했습니다.")
            
    def get_recommendations(self):
        if len(self.ratings) < 5:
            messagebox.showwarning(
                "경고",
                "추천을 받으려면 최소 5개 이상의 곡을 평가해야 합니다.\n"
                f"현재 평가한 곡 수: {len(self.ratings)}"
            )
            return
            
        method = self.rec_method_var.get()
        if not method:
            messagebox.showerror("오류", "추천 방식을 선택해주세요.")
            return
            
        try:
            rec_count = int(self.rec_count_var.get())
            min_rating = float(self.min_rating_var.get())
        except ValueError:
            messagebox.showerror("오류", "올바른 추천 설정값을 입력해주세요.")
            return
            
        logging.info(f"추천 작 - 방식: {method}, 곡 수: {rec_count}, 최소 평점: {min_rating}")
        
        # 진행 태그 표시
        progress = ttk.Progressbar(self.recommendation_tab, mode='indeterminate')
        progress.pack(pady=5)
        progress.start()
        
        def recommend():
            try:
                recommendations = []
                
                if method == "협업 필터링" or method == "하이브리드":
                    cf_recs = self.collaborative_filtering()
                    recommendations.extend(cf_recs)
                    
                if method == "장르 기반" or method == "하이브리드":
                    genre_recs = self.genre_based()
                    recommendations.extend(genre_recs)
                    
                if method == "아티스트 기반" or method == "하이브리드":
                    artist_recs = self.artist_based()
                    recommendations.extend(artist_recs)
                    
                # 중복 제거 및 정렬
                recommendations = list(set(recommendations))
                recommendations = [r for r in recommendations if r[1] >= min_rating]
                recommendations.sort(key=lambda x: x[1], reverse=True)
                
                # 결과 표시
                self.rec_result.delete(1.0, tk.END)
                self.rec_result.insert(tk.END, f"=== {method} 추천 결과 ===\n")
                self.rec_result.insert(tk.END, f"최소 평점: {min_rating}점 이상\n\n")
                
                if not recommendations:
                    self.rec_result.insert(tk.END, "조건에 맞는 추천 곡이 없습니다.\n")
                    self.rec_result.insert(tk.END, "다른 설정으로 다시 시도해보세요.")
                else:
                    for i, (song, score) in enumerate(recommendations[:rec_count], 1):
                        self.rec_result.insert(tk.END, f"{i}. 🎵 {song}\n")
                        self.rec_result.insert(tk.END, f"   평점 예측: {score:.2f}점\n")
                        self.rec_result.insert(tk.END, f"   추천 신뢰도: {'★' * int(score)}\n\n")
                
            except Exception as e:
                logging.error(f"추천 중 오류 발생: {str(e)}")
                self.rec_result.delete(1.0, tk.END)
                self.rec_result.insert(tk.END, "추천 중 오류가 발생했습니다. 다시 시도해주세요.")
            
            finally:
                progress.stop()
                progress.destroy()
                logging.info(f"{Fore.GREEN}추천 완료{Style.RESET_ALL}")
            
        threading.Thread(target=recommend).start()
        
    def collaborative_filtering(self):
        logging.info("협업 필터링 모델 학습 중...")
        
        if len(self.ratings) < 5:
            logging.warning("평가 데이터가 부족하여 협업 필터링을 수행할 수 없습니다.")
            return []
            
        try:
            # SVD 모델 학습
            reader = Reader(rating_scale=(1, 5))
            data = Dataset.load_from_df(self.ratings[['user_id', 'song_id', 'rating']], reader)
            
            trainset = data.build_full_trainset()
            self.svd_model = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02)
            self.svd_model.fit(trainset)
            
            # 추천 생성
            recommendations = []
            rated_songs = set(self.ratings[self.ratings['user_id'] == self.current_user_id]['song_id'])
            
            for song_key, song_id in self.song_id_mapping.items():
                if song_id not in rated_songs:
                    try:
                        pred = self.svd_model.predict(self.current_user_id, song_id).est
                        recommendations.append((song_key, pred))
                    except Exception as e:
                        logging.error(f"예측 중 오류 발생: {str(e)}")
                        continue
            
            return recommendations
            
        except Exception as e:
            logging.error(f"협업 필터링 중 오류 발생: {str(e)}")
            return []
            
    def genre_based(self):
        logging.info("장르 기반 추천 계산 중...")
        
        # 장르별 평균 평점 계산
        genre_ratings = {}
        for genre in self.music_data:
            genre_songs = [song['title'] for song in self.music_data[genre]]
            ratings = [r for r in self.ratings['rating'] if r > 0]
            if ratings:
                genre_ratings[genre] = np.mean(ratings)
                
        # 추천 생성
        recommendations = []
        for genre, rating in genre_ratings.items():
            for song in self.music_data[genre]:
                song_info = f"{song['title']} - {song['artist']} ({song['genre']})"
                recommendations.append((song_info, rating))
                
        return recommendations
        
    def artist_based(self):
        logging.info("아티스트 기반 추천 계산 중...")
        
        # 아티스트별 평균 평점 계산
        artist_ratings = {}
        for genre in self.music_data:
            for song in self.music_data[genre]:
                artist = song['artist']
                if artist not in artist_ratings:
                    artist_ratings[artist] = []
                ratings = [r for r in self.ratings['rating'] if r > 3]
                artist_ratings[artist].extend(ratings)
                
        # 추천 생성
        recommendations = []
        for artist, ratings in artist_ratings.items():
            if ratings:
                avg_rating = np.mean(ratings)
                for genre in self.music_data:
                    for song in self.music_data[genre]:
                        if song['artist'] == artist:
                            song_info = f"{song['title']} - {artist} ({song['genre']})"
                            recommendations.append((song_info, avg_rating))
                            
        return recommendations
        
    def save_rating_history(self, genre, song_info, rating):
        history = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'genre': genre,
            'song_info': song_info,
            'rating': rating
        }
        
        try:
            with open('rating_history.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
            
        data.append(history)
        
        with open('rating_history.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_rating_history(self):
        try:
            with open('rating_history.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
            
    def refresh_history(self):
        history = self.load_rating_history()
        self.history_text.delete(1.0, tk.END)
        
        if not history:
            self.history_text.insert(tk.END, "아직 평가 기록이 없습니다.")
            return
            
        for entry in reversed(history):  # 최신 기록이 위에 오도록 역순으로 표시
            try:
                # 시간 정보 표시
                timestamp = entry.get('timestamp', '날짜 정보 없음')
                self.history_text.insert(tk.END, f"🕒 {timestamp}\n")
                
                # 곡 정보 표시
                if 'song_info' in entry:
                    song_info = entry['song_info']
                elif 'track' in entry and 'artist' in entry:
                    song_info = f"{entry['track']} - {entry['artist']}"
                else:
                    song_info = "곡 정보 없음"
                self.history_text.insert(tk.END, f"🎵 {song_info}\n")
                
                # 장르 정보 표시
                genre = entry.get('genre', '장르 정보 없음')
                self.history_text.insert(tk.END, f"🎸 {genre}\n")
                
                # 평점 표시 (이모지로 시각화)
                rating = int(entry.get('rating', 0))
                stars = "⭐" * rating
                self.history_text.insert(tk.END, f"평점: {stars} ({rating}점)\n")
                
                # 구분선 추가
                self.history_text.insert(tk.END, "─" * 40 + "\n\n")
            except Exception as e:
                logging.error(f"히스토리 항목 표시 중 오류 발생: {str(e)}")
                continue
            
    def update_stats(self):
        history = self.load_rating_history()
        self.stats_text.delete(1.0, tk.END)
        
        if not history:
            self.stats_text.insert(tk.END, "통계를 계산하기 위한 데이터가 부족합니다.")
            return
            
        # 기본 통계
        total_ratings = len(history)
        avg_rating = np.mean([entry['rating'] for entry in history])
        
        # 장르별 통계
        genre_stats = {}
        for entry in history:
            genre = entry['genre']
            if genre not in genre_stats:
                genre_stats[genre] = []
            genre_stats[genre].append(entry['rating'])
            
        # 통계 표시
        self.stats_text.insert(tk.END, f"=== 전체 통계 ===\n")
        self.stats_text.insert(tk.END, f"총 평가 수: {total_ratings}\n")
        self.stats_text.insert(tk.END, f"평균 평점: {avg_rating:.2f}\n\n")
        
        self.stats_text.insert(tk.END, f"=== 장르별 통계 ===\n")
        for genre, ratings in genre_stats.items():
            avg = np.mean(ratings)
            count = len(ratings)
            self.stats_text.insert(tk.END, f"{genre}:\n")
            self.stats_text.insert(tk.END, f"  평가 수: {count}\n")
            self.stats_text.insert(tk.END, f"  평균 평점: {avg:.2f}\n")
            self.stats_text.insert(tk.END, f"  선호도: {'★' * int(avg)}\n\n")
            
    def create_playlist(self):
        # 플레이리스트 생성 다이얼로그
        dialog = tk.Toplevel(self.root)
        dialog.title("새 플레이리스트")
        dialog.geometry("400x150")
        dialog.configure(bg=self.style.COLORS['bg_dark'])
        
        # 다이얼로그를 모달로 설정
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 입력 프레임
        input_frame = ttk.Frame(dialog, style="Custom.TFrame")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 레이블
        ttk.Label(
            input_frame,
            text="플레이리스트 이름:",
            style="Custom.TLabel"
        ).pack(pady=(0, 10))
        
        # 입력 필드
        name_var = tk.StringVar()
        name_entry = ttk.Entry(
            input_frame,
            textvariable=name_var,
            width=40
        )
        name_entry.pack(pady=(0, 20))
        name_entry.focus()
        
        def save_playlist():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning(
                    "경고",
                    "플레이리스트 이름을 입력해주세요.",
                    parent=dialog
                )
                return
                
            # 중복 확인
            existing_playlists = list(self.playlist_listbox.get(0, tk.END))
            if name in existing_playlists:
                messagebox.showwarning(
                    "경고",
                    "이미 존재하는 플레이리스트 이름입니다.",
                    parent=dialog
                )
                return
                
            # 플레이리스트 추가
            self.playlist_listbox.insert(tk.END, name)
            self.save_playlists()
            
            # 성공 메시지
            messagebox.showinfo(
                "성공",
                f"'{name}' 플레이리스트가 생성되었습니다.",
                parent=dialog
            )
            dialog.destroy()
        
        # 버튼 프레임
        btn_frame = ttk.Frame(input_frame, style="Custom.TFrame")
        btn_frame.pack(fill=tk.X)
        
        # 확인 버튼
        ttk.Button(
            btn_frame,
            text="확인",
            command=save_playlist,
            style="Custom.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # 취소 버튼
        ttk.Button(
            btn_frame,
            text="취소",
            command=dialog.destroy,
            style="Custom.TButton"
        ).pack(side=tk.LEFT)
        
        # Enter 키 바인딩
        dialog.bind('<Return>', lambda e: save_playlist())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # 다이얼로그가 닫힐 때까지 대기
        dialog.wait_window()

    def add_to_playlist(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "플레이리스트를 선택해주세요.")
            return
            
        # 곡 선택 다이얼로그 표시
        dialog = tk.Toplevel(self.root)
        dialog.title("곡 선택")
        dialog.geometry("400x500")
        
        # 곡 목록 표시
        song_list = tk.Listbox(
            dialog,
            bg=self.style.COLORS['bg_light'],
            fg=self.style.COLORS['text'],
            selectmode=tk.MULTIPLE,
            font=self.style.FONTS['normal']
        )
        song_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 모든 곡 추가
        for genre in self.music_data:
            for song in self.music_data[genre]:
                song_list.insert(tk.END, f"{song['title']} - {song['artist']}")
        
        def confirm_selection():
            selections = song_list.curselection()
            if selections:
                # 선택된 곡들 저장
                playlist_name = self.playlist_listbox.get(selection[0])
                selected_songs = [song_list.get(idx) for idx in selections]
                self.save_playlist_songs(playlist_name, selected_songs)
                dialog.destroy()
                messagebox.showinfo("성공", "선택한 곡들이 플레이리스트에 추가되었습니다.")
        
        ttk.Button(
            dialog,
            text="확인",
            command=confirm_selection,
            style="Custom.TButton"
        ).pack(pady=10)

    def share_playlist(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "공유할 플레이리스트를 선택해주세요.")
            return
            
        playlist_name = self.playlist_listbox.get(selection[0])
        songs = self.load_playlist_songs(playlist_name)
        
        if not songs:
            messagebox.showwarning("경고", "플레이리스트가 비어있습니다.")
            return
            
        # 공유 링크 생성 (예시)
        share_text = f"내 플레이리스트 '{playlist_name}' 공유합니다!\n\n"
        for i, song in enumerate(songs, 1):
            share_text += f"{i}. {song}\n"
            
        # 클립보드에 복사
        self.root.clipboard_clear()
        self.root.clipboard_append(share_text)
        messagebox.showinfo("공유", "플레이리스트가 클립보드에 복사되었습니다.")

    def update_trends(self):
        history = self.load_rating_history()
        if not history:
            messagebox.showwarning("경고", "트렌드를 분석할 데이터가 부족합니다.")
            return
            
        # 차트 초기화
        self.fig.clear()
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)
        
        # 장르별 평균 평점
        genre_ratings = {}
        for entry in history:
            genre = entry['genre']
            if genre not in genre_ratings:
                genre_ratings[genre] = []
            genre_ratings[genre].append(entry['rating'])
            
        genres = list(genre_ratings.keys())
        averages = [np.mean(ratings) for ratings in genre_ratings.values()]
        
        # 장르별 평균 평점 차트
        bars = ax1.bar(genres, averages, color=self.style.COLORS['chart_colors'])
        ax1.set_title('장르별 평균 평점', color=self.style.COLORS['text'])
        ax1.set_ylabel('평균 평점', color=self.style.COLORS['text'])
        ax1.tick_params(colors=self.style.COLORS['text'])
        
        # 평가 추이
        timestamps = [datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') for entry in history]
        ratings = [entry['rating'] for entry in history]
        
        ax2.plot(timestamps, ratings, 'o-', color=self.style.COLORS['accent'])
        ax2.set_title('평가 추이', color=self.style.COLORS['text'])
        ax2.set_ylabel('평점', color=self.style.COLORS['text'])
        ax2.tick_params(colors=self.style.COLORS['text'])
        
        self.fig.tight_layout()
        self.fig.canvas.draw()

    def save_playlists(self):
        playlists = list(self.playlist_listbox.get(0, tk.END))
        with open('playlists.json', 'w', encoding='utf-8') as f:
            json.dump(playlists, f, ensure_ascii=False, indent=2)

    def load_playlists(self):
        try:
            with open('playlists.json', 'r', encoding='utf-8') as f:
                playlists = json.load(f)
                for playlist in playlists:
                    self.playlist_listbox.insert(tk.END, playlist)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_playlist_songs(self, playlist_name, songs):
        filename = f'playlist_{playlist_name}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)

    def load_playlist_songs(self, playlist_name):
        try:
            filename = f'playlist_{playlist_name}.json'
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def show_welcome_message(self):
        messagebox.showinfo(
            "환영합니다",
            "Music Recommender Pro 3.0에 오신 것을 환영합니다!\n\n"
            "새로운 기능:\n"
            "- 플레이리스트 관리\n"
            "- 트렌드 분석\n"
            "- 향상된 추천 알고리즘\n\n"
            "개발자: FAYA\n"
            "버전: 3.0.0"
        )

    def run(self):
        logging.info(f"{Fore.CYAN}Music Recommender Pro 시작{Style.RESET_ALL}")
        self.root.mainloop()

    def delete_playlist(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "삭제할 플레이리스트를 선택해주세요.")
            return
            
        playlist_name = self.playlist_listbox.get(selection[0])
        if messagebox.askyesno("확인", f"'{playlist_name}' 플레이리스트를 삭제하시겠습니까?"):
            # 플레이리스트 파일 삭제
            try:
                os.remove(f'playlist_{playlist_name}.json')
            except:
                pass
                
            # 리스트에서 제거
            self.playlist_listbox.delete(selection[0])
            self.save_playlists()
            messagebox.showinfo("성공", f"'{playlist_name}' 플레이리스트가 삭제되었습니다.")

if __name__ == "__main__":
    print(f"{Fore.CYAN}=== Music Recommender Pro 초기화 중... ==={Style.RESET_ALL}")
    print(f"{Fore.GREEN}Version: 3.0.0{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}개발자: faya{Style.RESET_ALL}")
    print("-" * 50)
    
    try:
        app = MusicRecommender()
        app.run()
    except Exception as e:
        logging.error(f"{Fore.RED}오류 발생: {str(e)}{Style.RESET_ALL}")
        raise 