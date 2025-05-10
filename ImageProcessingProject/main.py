import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Scale, HORIZONTAL
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageChops
import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class GoruntuIslemeUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Görüntü İşleme Uygulaması")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        # Ana görüntü değişkenleri
        self.orjinal_goruntu = None
        self.guncel_goruntu = None
        self.goruntu_yolu = None
        self.tk_orjinal_goruntu = None
        self.tk_guncel_goruntu = None
        self.cv2_goruntu = None

        # Perspektif düzeltme için değişkenler
        self.perspektif_noktalar = []
        self.perspektif_mod = False
        self.gecici_nokta = None

        # Ana çerçeveleri oluştur
        self.ust_panel = tk.Frame(root, bg="#f0f0f0", height=50)
        self.ust_panel.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.alt_panel = tk.Frame(root, bg="#f0f0f0")
        self.alt_panel.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buton panelleri
        self.buton_panel = tk.Frame(self.alt_panel, bg="#dcdcdc", width=200)
        self.buton_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Görüntü alanı panel
        self.goruntu_panel = tk.Frame(self.alt_panel, bg="#f0f0f0")
        self.goruntu_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # İki görüntü için çerçeveler oluştur
        self.orjinal_frame = tk.LabelFrame(self.goruntu_panel, text="Orijinal Görüntü", bg="#f0f0f0", padx=5, pady=5)
        self.orjinal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.islem_frame = tk.LabelFrame(self.goruntu_panel, text="İşlenmiş Görüntü", bg="#f0f0f0", padx=5, pady=5)
        self.islem_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Görüntü alanları
        self.orjinal_goruntu_alani = tk.Label(self.orjinal_frame, bg="white", relief=tk.SUNKEN)
        self.orjinal_goruntu_alani.pack(fill=tk.BOTH, expand=True)

        self.islem_goruntu_alani = tk.Label(self.islem_frame, bg="white", relief=tk.SUNKEN)
        self.islem_goruntu_alani.pack(fill=tk.BOTH, expand=True)

        # Canvas'ı perspektif düzeltme için bağla
        self.islem_goruntu_alani.bind("<Button-1>", self.perspektif_nokta_ekle)

        # Durum çubuğu
        self.durum_cubugu = tk.Label(root, text="Hazır", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.durum_cubugu.pack(side=tk.BOTTOM, fill=tk.X)

        # Menü çubuğu oluştur
        self.menu_olustur()

        # Butonları oluştur
        self.butonlari_olustur()

        # Son uygulanan işlemin adını sakla
        self.son_islem = None

        # Histogram penceresi
        self.histogram_penceresi = None
        self.histogram_fig = None
        self.histogram_canvas = None

    def menu_olustur(self):
        menu_cubugu = tk.Menu(self.root)
        self.root.config(menu=menu_cubugu)

        # Dosya menüsü
        dosya_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Dosya", menu=dosya_menu)
        dosya_menu.add_command(label="Görüntü Aç", command=self.goruntu_yukle)
        dosya_menu.add_command(label="Görüntü Aç (Gri Tonlama)", command=self.goruntu_yukle_gri)
        dosya_menu.add_command(label="Görüntüyü Kaydet", command=self.goruntu_kaydet)
        dosya_menu.add_separator()
        dosya_menu.add_command(label="Çıkış", command=self.root.quit)

        # RGB menüsü
        rgb_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="RGB Kanalları", menu=rgb_menu)
        rgb_menu.add_command(label="R Kanalını Göster", command=lambda: self.rgb_kanal_goster('R'))
        rgb_menu.add_command(label="G Kanalını Göster", command=lambda: self.rgb_kanal_goster('G'))
        rgb_menu.add_command(label="B Kanalını Göster", command=lambda: self.rgb_kanal_goster('B'))
        rgb_menu.add_command(label="Tüm Kanalları Göster", command=self.rgb_tum_kanallari_goster)

        # Histogram menüsü
        histogram_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Histogram", menu=histogram_menu)
        histogram_menu.add_command(label="Histogram Göster", command=self.histogram_goster)
        histogram_menu.add_command(label="Histogram Eşitleme", command=self.histogram_esitleme)

        # Dönüşüm menüsü
        transform_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Dönüşümler", menu=transform_menu)
        transform_menu.add_command(label="Taşıma", command=self.tasima_dialog)
        transform_menu.add_command(label="Eğme (Shearing)", command=self.egme_dialog)
        transform_menu.add_command(label="Ölçekleme", command=self.olcekleme_dialog)
        transform_menu.add_command(label="Kırpma", command=self.kirpma_dialog)
        transform_menu.add_command(label="Perspektif Düzeltme", command=self.perspektif_duzeltme_baslat)

        # Filtreleme menüsü
        filtre_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Filtreler", menu=filtre_menu)

        # Uzamsal filtreler alt menüsü
        uzamsal_filtre_menu = tk.Menu(filtre_menu, tearoff=0)
        filtre_menu.add_cascade(label="Uzamsal Filtreler", menu=uzamsal_filtre_menu)
        uzamsal_filtre_menu.add_command(label="Ortalama Filtre", command=self.ortalama_filtre_dialog)
        uzamsal_filtre_menu.add_command(label="Medyan Filtre", command=self.medyan_filtre_dialog)
        uzamsal_filtre_menu.add_command(label="Gauss Filtresi", command=self.gauss_filtre_dialog)
        uzamsal_filtre_menu.add_command(label="Konservatif Filtreleme", command=self.konservatif_filtre)
        uzamsal_filtre_menu.add_command(label="Crimmins Speckle", command=self.crimmins_speckle)

        # Frekans filtreler alt menüsü
        frekans_filtre_menu = tk.Menu(filtre_menu, tearoff=0)
        filtre_menu.add_cascade(label="Frekans Filtreleri", menu=frekans_filtre_menu)
        frekans_filtre_menu.add_command(label="Fourier LPF", command=self.fourier_lpf_dialog)
        frekans_filtre_menu.add_command(label="Fourier HPF", command=self.fourier_hpf_dialog)
        frekans_filtre_menu.add_command(label="Band Geçiren Filtre", command=self.band_geciren_dialog)
        frekans_filtre_menu.add_command(label="Band Durduran Filtre", command=self.band_durduran_dialog)
        frekans_filtre_menu.add_command(label="Butterworth LPF", command=self.butterworth_lpf_dialog)
        frekans_filtre_menu.add_command(label="Butterworth HPF", command=self.butterworth_hpf_dialog)
        frekans_filtre_menu.add_command(label="Gaussian LPF", command=self.gaussian_lpf_dialog)
        frekans_filtre_menu.add_command(label="Gaussian HPF", command=self.gaussian_hpf_dialog)
        frekans_filtre_menu.add_command(label="Homomorfik Filtre", command=self.homomorfik_filtre_dialog)

        # Kenar Algılama menüsü
        kenar_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Kenar Algılama", menu=kenar_menu)
        kenar_menu.add_command(label="Sobel", command=self.sobel_kenar_algilama)
        kenar_menu.add_command(label="Prewitt", command=self.prewitt_kenar_algilama)
        kenar_menu.add_command(label="Roberts Cross", command=self.roberts_cross_algilama)
        kenar_menu.add_command(label="Compass", command=self.compass_kenar_algilama)
        kenar_menu.add_command(label="Canny", command=self.canny_kenar_dialog)
        kenar_menu.add_command(label="Laplace", command=self.laplace_kenar_algilama)
        kenar_menu.add_command(label="Gabor", command=self.gabor_filtre_dialog)

        # Morfolojik İşlemler menüsü (Kenar Algılama menüsünden sonra ekleyin)
        morfoloji_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Morfolojik İşlemler", menu=morfoloji_menu)
        morfoloji_menu.add_command(label="Erosion (Aşındırma)", command=self.erosion_dialog)
        morfoloji_menu.add_command(label="Dilation (Genişletme)", command=self.dilation_dialog)

        # Geometri Algılama menüsü
        geometri_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Geometri Algılama", menu=geometri_menu)
        geometri_menu.add_command(label="Hough Doğru", command=self.hough_line_dialog)
        geometri_menu.add_command(label="Hough Çember", command=self.hough_circle_dialog)

        # Segmentasyon menüsü
        segmentation_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Segmentasyon", menu=segmentation_menu)
        segmentation_menu.add_command(label="K-Means", command=self.kmeans_segmentation_dialog)

        # Yardım menüsü
        yardim_menu = tk.Menu(menu_cubugu, tearoff=0)
        menu_cubugu.add_cascade(label="Yardım", menu=yardim_menu)
        yardim_menu.add_command(label="Hakkında", command=self.hakkinda_goster)

    def butonlari_olustur(self):
        # Üst panel butonları
        yukle_btn = ttk.Button(self.ust_panel, text="Görüntü Yükle", command=self.goruntu_yukle)
        yukle_btn.pack(side=tk.LEFT, padx=5, pady=5)

        yukle_gri_btn = ttk.Button(self.ust_panel, text="Görüntü Yükle (Gri)", command=self.goruntu_yukle_gri)
        yukle_gri_btn.pack(side=tk.LEFT, padx=5, pady=5)

        kaydet_btn = ttk.Button(self.ust_panel, text="Görüntüyü Kaydet", command=self.goruntu_kaydet)
        kaydet_btn.pack(side=tk.LEFT, padx=5, pady=5)

        temizle_btn = ttk.Button(self.ust_panel, text="İşlemi Temizle", command=self.islemi_temizle)
        temizle_btn.pack(side=tk.LEFT, padx=5, pady=5)

        orjinale_don_btn = ttk.Button(self.ust_panel, text="Orijinale Dön", command=self.orjinale_don)
        orjinale_don_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Buton paneli için başlık
        baslik = tk.Label(self.buton_panel, text="İşlemler", bg="#dcdcdc", font=("Arial", 12, "bold"))
        baslik.pack(pady=10)

        # İşlem butonları - daha kompakt tasarım için
        # Butonları gruplandırmak için çerçeveler oluştur
        temel_islemler_frame = tk.LabelFrame(self.buton_panel, text="Temel İşlemler", bg="#dcdcdc", padx=5, pady=5)
        temel_islemler_frame.pack(fill=tk.X, padx=5, pady=5)

        renk_islemleri_frame = tk.LabelFrame(self.buton_panel, text="Renk İşlemleri", bg="#dcdcdc", padx=5, pady=5)
        renk_islemleri_frame.pack(fill=tk.X, padx=5, pady=5)

        filtre_islemleri_frame = tk.LabelFrame(self.buton_panel, text="Filtreler", bg="#dcdcdc", padx=5, pady=5)
        filtre_islemleri_frame.pack(fill=tk.X, padx=5, pady=5)

        donusum_islemleri_frame = tk.LabelFrame(self.buton_panel, text="Dönüşümler", bg="#dcdcdc", padx=5, pady=5)
        donusum_islemleri_frame.pack(fill=tk.X, padx=5, pady=5)

        # Temel işlem butonları
        temel_islemler = [
            ("Döndürme (90°)", self.dondurme),
            ("Aynalama", self.aynalama),
            ("Perspektif", self.perspektif_duzeltme_baslat),
            ("Eşikleme", self.esikleme_dialog)
        ]

        for i, (text, command) in enumerate(temel_islemler):
            btn = ttk.Button(temel_islemler_frame, text=text, command=command, width=12)
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")

        # Renk işlem butonları
        renk_islemleri = [
            ("Gri Tonlama", self.gri_tonlama),
            ("Negatif", self.negatif),
            ("Parlaklık +", self.parlaklik_artir),
            ("Parlaklık -", self.parlaklik_azalt),
            ("Kontrast +", self.kontrast_artir),
            ("Kontrast -", self.kontrast_azalt)
        ]

        for i, (text, command) in enumerate(renk_islemleri):
            btn = ttk.Button(renk_islemleri_frame, text=text, command=command, width=12)
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")

        # Filtre işlem butonları
        filtre_islemleri = [
            ("Bulanıklaştırma", self.bulaniklastirma),
            ("Keskinleştirme", self.keskinlestirme),
            ("Kenar Algılama", self.kenar_algilama),
            ("Histogram", self.histogram_goster)
        ]

        for i, (text, command) in enumerate(filtre_islemleri):
            btn = ttk.Button(filtre_islemleri_frame, text=text, command=command, width=12)
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")

        # Dönüşüm işlem butonları
        donusum_islemleri = [
            ("Taşıma", self.tasima_dialog),
            ("Eğme", self.egme_dialog),
            ("Ölçekleme", self.olcekleme_dialog),
            ("Kırpma", self.kirpma_dialog)
        ]

        for i, (text, command) in enumerate(donusum_islemleri):
            btn = ttk.Button(donusum_islemleri_frame, text=text, command=command, width=12)
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")

        # Morfolojik işlemler frame'i (filtre_islemleri_frame'den sonra ekleyin)
        morfoloji_islemleri_frame = tk.LabelFrame(self.buton_panel, text="Morfolojik İşlemler", bg="#dcdcdc", padx=5, pady=5)
        morfoloji_islemleri_frame.pack(fill=tk.X, padx=5, pady=5)

        # Morfolojik işlem butonları
        morfoloji_islemleri = [
            ("Erosion", self.erosion_dialog),
            ("Dilation", self.dilation_dialog)
        ]

        for i, (text, command) in enumerate(morfoloji_islemleri):
            btn = ttk.Button(morfoloji_islemleri_frame, text=text, command=command, width=12)
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")

    def goruntu_yukle(self, gri_mod=False):
        self.goruntu_yolu = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        )

        if self.goruntu_yolu:
            try:
                if gri_mod:
                    self.orjinal_goruntu = Image.open(self.goruntu_yolu).convert('L').convert('RGB')
                else:
                    self.orjinal_goruntu = Image.open(self.goruntu_yolu).convert('RGB')

                self.guncel_goruntu = self.orjinal_goruntu.copy()

                # OpenCV formatında görüntüyü sakla
                self.cv2_goruntu = cv2.imread(self.goruntu_yolu)

                # Her iki görüntüyü de göster
                self.goruntuleri_goster()

                self.durum_cubugu.config(text=f"Görüntü yüklendi: {os.path.basename(self.goruntu_yolu)}")
                self.son_islem = None
            except Exception as e:
                messagebox.showerror("Hata", f"Görüntü yüklenirken hata oluştu: {str(e)}")

    def goruntu_yukle_gri(self):
        self.goruntu_yukle(gri_mod=True)

    def goruntuleri_goster(self):
        if self.orjinal_goruntu and self.guncel_goruntu:
            # Orijinal görüntüyü göster
            self.tk_orjinal_goruntu = self.goruntu_formatla(self.orjinal_goruntu, self.orjinal_goruntu_alani)
            self.orjinal_goruntu_alani.config(image=self.tk_orjinal_goruntu)
            self.orjinal_goruntu_alani.image = self.tk_orjinal_goruntu

            # İşlenmiş görüntüyü göster
            self.tk_guncel_goruntu = self.goruntu_formatla(self.guncel_goruntu, self.islem_goruntu_alani)
            self.islem_goruntu_alani.config(image=self.tk_guncel_goruntu)
            self.islem_goruntu_alani.image = self.tk_guncel_goruntu

    def goruntu_formatla(self, goruntu, goruntu_alani):
        """Görüntüyü görüntüleme alanına uygun şekilde yeniden boyutlandırır"""
        genislik = goruntu_alani.winfo_width()
        yukseklik = goruntu_alani.winfo_height()

        # Eğer genişlik ve yükseklik henüz belirlenmemişse varsayılan değerler kullan
        if genislik <= 1:
            genislik = 500
        if yukseklik <= 1:
            yukseklik = 400

        # En-boy oranını koru
        goruntu_orani = goruntu.width / goruntu.height
        alan_orani = genislik / yukseklik

        if goruntu_orani > alan_orani:
            yeni_genislik = genislik
            yeni_yukseklik = int(genislik / goruntu_orani)
        else:
            yeni_yukseklik = yukseklik
            yeni_genislik = int(yukseklik * goruntu_orani)

        boyutlandirilmis_goruntu = goruntu.resize((yeni_genislik, yeni_yukseklik), Image.LANCZOS)
        return ImageTk.PhotoImage(boyutlandirilmis_goruntu)

    def goruntu_islem_uygula(self, islem_fonksiyonu):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        try:
            # İşlemi uygula
            self.guncel_goruntu = islem_fonksiyonu(self.guncel_goruntu)

            # Güncel görüntüyü göster - sadece işlenmiş görüntüyü güncelle
            self.tk_guncel_goruntu = self.goruntu_formatla(self.guncel_goruntu, self.islem_goruntu_alani)
            self.islem_goruntu_alani.config(image=self.tk_guncel_goruntu)
            self.islem_goruntu_alani.image = self.tk_guncel_goruntu

            # Son işlemi kaydet
            self.son_islem = islem_fonksiyonu.__name__

            # Durum çubuğunu güncelle
            self.durum_cubugu.config(text=f"İşlem uygulandı: {self.son_islem}")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem uygulanırken hata oluştu: {str(e)}")

    def islemi_temizle(self):
        """Son işlemi temizler ve orijinal görüntüye geri döner"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Yüklenmiş bir görüntü yok")
            return

        if self.son_islem:
            self.guncel_goruntu = self.orjinal_goruntu.copy()

            # Görüntüleri güncelle
            self.tk_guncel_goruntu = self.goruntu_formatla(self.guncel_goruntu, self.islem_goruntu_alani)
            self.islem_goruntu_alani.config(image=self.tk_guncel_goruntu)
            self.islem_goruntu_alani.image = self.tk_guncel_goruntu

            self.durum_cubugu.config(text="İşlemler temizlendi, orijinal görüntüye dönüldü")
            self.son_islem = None
        else:
            self.durum_cubugu.config(text="Temizlenecek işlem yok")

    # ----------------- RGB Kanalları İşlemleri -----------------

    def rgb_kanal_goster(self, kanal):
        """Belirtilen RGB kanalını gösterir (R, G veya B)"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        try:
            # RGB kanallarını ayır
            r, g, b = self.guncel_goruntu.split()

            # Seçilen kanalı göster, diğerlerini sıfırla
            if kanal == 'R':
                def islem(goruntu):
                    r, g, b = goruntu.split()
                    return Image.merge("RGB", (r, Image.new("L", r.size, 0), Image.new("L", r.size, 0)))
            elif kanal == 'G':
                def islem(goruntu):
                    r, g, b = goruntu.split()
                    return Image.merge("RGB", (Image.new("L", g.size, 0), g, Image.new("L", g.size, 0)))
            else:  # B kanalı
                def islem(goruntu):
                    r, g, b = goruntu.split()
                    return Image.merge("RGB", (Image.new("L", b.size, 0), Image.new("L", b.size, 0), b))

            self.goruntu_islem_uygula(islem)
            self.durum_cubugu.config(text=f"{kanal} kanalı gösteriliyor")
        except Exception as e:
            print(f"RGB Kanal Hatası: {str(e)}")  # Hata mesajını konsola yazdır
            messagebox.showerror("Hata", f"RGB kanalı gösterilirken hata oluştu: {str(e)}")

    def rgb_tum_kanallari_goster(self):
        """RGB kanallarını ayrı pencerede göster"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        try:
            # RGB kanallarını ayır
            r, g, b = self.guncel_goruntu.split()

            # Her kanal için yeni bir görüntü oluştur
            r_goruntu = Image.merge("RGB", (r, Image.new("L", r.size, 0), Image.new("L", r.size, 0)))
            g_goruntu = Image.merge("RGB", (Image.new("L", g.size, 0), g, Image.new("L", g.size, 0)))
            b_goruntu = Image.merge("RGB", (Image.new("L", b.size, 0), Image.new("L", b.size, 0), b))

            # Yeni pencere - sınıf değişkeni olarak sakla
            self.rgb_pencere = tk.Toplevel(self.root)
            self.rgb_pencere.title("RGB Kanalları")
            self.rgb_pencere.geometry("900x350")

            # Çerçeveler
            r_frame = tk.LabelFrame(self.rgb_pencere, text="R Kanalı", padx=5, pady=5)
            r_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            g_frame = tk.LabelFrame(self.rgb_pencere, text="G Kanalı", padx=5, pady=5)
            g_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            b_frame = tk.LabelFrame(self.rgb_pencere, text="B Kanalı", padx=5, pady=5)
            b_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Görüntüleri yeniden boyutlandır
            boyut = (250, 250)
            r_boyutlandirilmis = r_goruntu.resize(boyut, Image.LANCZOS)
            g_boyutlandirilmis = g_goruntu.resize(boyut, Image.LANCZOS)
            b_boyutlandirilmis = b_goruntu.resize(boyut, Image.LANCZOS)

            # PhotoImage nesneleri - sınıf değişkenleri olarak sakla
            self.r_tk = ImageTk.PhotoImage(r_boyutlandirilmis)
            self.g_tk = ImageTk.PhotoImage(g_boyutlandirilmis)
            self.b_tk = ImageTk.PhotoImage(b_boyutlandirilmis)

            # Etiketlerde göster
            r_label = tk.Label(r_frame, image=self.r_tk)
            r_label.image = self.r_tk  # Referans tut
            r_label.pack(fill=tk.BOTH, expand=True)

            g_label = tk.Label(g_frame, image=self.g_tk)
            g_label.image = self.g_tk  # Referans tut
            g_label.pack(fill=tk.BOTH, expand=True)

            b_label = tk.Label(b_frame, image=self.b_tk)
            b_label.image = self.b_tk  # Referans tut
            b_label.pack(fill=tk.BOTH, expand=True)

            self.durum_cubugu.config(text="RGB kanalları görüntüleniyor")
        except Exception as e:
            print(f"RGB Tüm Kanallar Hatası: {str(e)}")  # Hata mesajını konsola yazdır
            messagebox.showerror("Hata", f"RGB kanalları gösterilirken hata oluştu: {str(e)}")

    # ----------------- Histogram İşlemleri -----------------

    def histogram_goster(self):
        """Görüntünün histogramını gösterir"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        try:
            # Eğer histogram penceresi açıksa kapat
            if self.histogram_penceresi and self.histogram_penceresi.winfo_exists():
                self.histogram_penceresi.destroy()

            # Histogram hesapla
            gri_goruntu = self.guncel_goruntu.convert('L')
            hist = gri_goruntu.histogram()[:256]  # Sadece gri tonlar (0-255)

            # Yeni pencere oluştur
            self.histogram_penceresi = tk.Toplevel(self.root)
            self.histogram_penceresi.title("Histogram")
            self.histogram_penceresi.geometry("600x400")

            # Matplotlib figure oluştur
            self.histogram_fig = plt.Figure(figsize=(6, 4), dpi=100)
            ax = self.histogram_fig.add_subplot(111)
            ax.bar(range(256), hist, width=1, color='gray')
            ax.set_xlim([0, 255])
            ax.set_title('Görüntü Histogramı')
            ax.set_xlabel('Piksel Değeri')
            ax.set_ylabel('Frekans')

            # Canvas oluştur
            self.histogram_canvas = FigureCanvasTkAgg(self.histogram_fig, master=self.histogram_penceresi)
            self.histogram_canvas.draw()
            self.histogram_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.durum_cubugu.config(text="Histogram görüntüleniyor")
        except Exception as e:
            messagebox.showerror("Hata", f"Histogram gösterilirken hata oluştu: {str(e)}")

    def histogram_esitleme(self):
        """Histogram eşitleme uygula"""

        def islem(goruntu):
            # Görüntüyü gri tonlamalı yap
            gri_goruntu = goruntu.convert('L')
            # Histogram eşitleme uygula
            esitlenmis = ImageOps.equalize(gri_goruntu)
            # RGB moduna geri dön
            return esitlenmis.convert('RGB')

        self.goruntu_islem_uygula(islem)

    # ----------------- Temel Görüntü İşleme Fonksiyonları -----------------

    def gri_tonlama(self):
        def islem(goruntu):
            return ImageOps.grayscale(goruntu).convert("RGB")

        self.goruntu_islem_uygula(islem)

    def bulaniklastirma(self):
        def islem(goruntu):
            return goruntu.filter(ImageFilter.BLUR)

        self.goruntu_islem_uygula(islem)

    def keskinlestirme(self):
        def islem(goruntu):
            return goruntu.filter(ImageFilter.SHARPEN)

        self.goruntu_islem_uygula(islem)

    def negatif(self):
        def islem(goruntu):
            return ImageOps.invert(goruntu)

        self.goruntu_islem_uygula(islem)

    def dondurme(self):
        def islem(goruntu):
            return goruntu.rotate(90, expand=True)

        self.goruntu_islem_uygula(islem)

    def aynalama(self):
        def islem(goruntu):
            return ImageOps.mirror(goruntu)

        self.goruntu_islem_uygula(islem)

    def parlaklik_artir(self):
        def islem(goruntu):
            parlaklik_faktor = 1.3  # %30 artış
            enhancer = ImageEnhance.Brightness(goruntu)
            return enhancer.enhance(parlaklik_faktor)

        self.goruntu_islem_uygula(islem)

    def parlaklik_azalt(self):
        def islem(goruntu):
            parlaklik_faktor = 0.7  # %30 azalış
            enhancer = ImageEnhance.Brightness(goruntu)
            return enhancer.enhance(parlaklik_faktor)

        self.goruntu_islem_uygula(islem)

    def kontrast_artir(self):
        def islem(goruntu):
            kontrast_faktor = 1.5
            enhancer = ImageEnhance.Contrast(goruntu)
            return enhancer.enhance(kontrast_faktor)

        self.goruntu_islem_uygula(islem)

    def kontrast_azalt(self):
        def islem(goruntu):
            kontrast_faktor = 0.5
            enhancer = ImageEnhance.Contrast(goruntu)
            return enhancer.enhance(kontrast_faktor)

        self.goruntu_islem_uygula(islem)

    def kenar_algilama(self):
        def islem(goruntu):
            return goruntu.filter(ImageFilter.FIND_EDGES)

        self.goruntu_islem_uygula(islem)

    def orjinale_don(self):
        if self.orjinal_goruntu:
            self.guncel_goruntu = self.orjinal_goruntu.copy()

            # Görüntüleri güncelle
            self.tk_guncel_goruntu = self.goruntu_formatla(self.guncel_goruntu, self.islem_goruntu_alani)
            self.islem_goruntu_alani.config(image=self.tk_guncel_goruntu)
            self.islem_goruntu_alani.image = self.tk_guncel_goruntu

            self.durum_cubugu.config(text="Orijinal görüntüye dönüldü")
            self.son_islem = None

    def goruntu_kaydet(self):
        if self.guncel_goruntu is None:
            messagebox.showinfo("Bilgi", "Kaydedilecek görüntü yok")
            return

        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All files", "*.*")]
        )

        if dosya_yolu:
            try:
                self.guncel_goruntu.save(dosya_yolu)
                self.durum_cubugu.config(text=f"Görüntü kaydedildi: {os.path.basename(dosya_yolu)}")
            except Exception as e:
                messagebox.showerror("Hata", f"Görüntü kaydedilirken hata oluştu: {str(e)}")

        # ----------------- Eşikleme İşlemi -----------------

    def esikleme_dialog(self):
        """Eşik değeri seçme dialogu gösterir"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        esik_pencere = tk.Toplevel(self.root)
        esik_pencere.title("Eşikleme")
        esik_pencere.geometry("400x150")
        esik_pencere.resizable(False, False)

        # Eşik değeri için kayar çubuk
        esik_frame = tk.Frame(esik_pencere)
        esik_frame.pack(pady=20)

        esik_label = tk.Label(esik_frame, text="Eşik Değeri:")
        esik_label.pack(side=tk.LEFT, padx=10)

        esik_deger = tk.IntVar(value=128)
        esik_slider = Scale(esik_frame, from_=0, to=255, orient=HORIZONTAL,
                                length=200, variable=esik_deger)
        esik_slider.pack(side=tk.LEFT, padx=10)

        # Uygula butonu
        def esikleme_uygula():
            esik = esik_deger.get()

            def islem(goruntu):
                # Gri tonlamalı görüntüye dönüştür
                gri_goruntu = goruntu.convert('L')
                # Eşikleme uygula
                return gri_goruntu.point(lambda x: 255 if x > esik else 0).convert('RGB')

            self.goruntu_islem_uygula(islem)
            esik_pencere.destroy()

        buton_frame = tk.Frame(esik_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=esikleme_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=esik_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # ----------------- Dönüşüm İşlemleri -----------------

    def tasima_dialog(self):
        """Taşıma işlemi için dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        tasima_pencere = tk.Toplevel(self.root)
        tasima_pencere.title("Taşıma")
        tasima_pencere.geometry("350x200")
        tasima_pencere.resizable(False, False)

        # X ve Y ofset değerleri için giriş alanları
        ofset_frame = tk.Frame(tasima_pencere)
        ofset_frame.pack(pady=20)

        tk.Label(ofset_frame, text="X Ofset:").grid(row=0, column=0, padx=10, pady=5)
        x_ofset = tk.StringVar(value="50")
        tk.Entry(ofset_frame, textvariable=x_ofset, width=10).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(ofset_frame, text="Y Ofset:").grid(row=1, column=0, padx=10, pady=5)
        y_ofset = tk.StringVar(value="50")
        tk.Entry(ofset_frame, textvariable=y_ofset, width=10).grid(row=1, column=1, padx=10, pady=5)

        # Uygula butonu
        def tasima_uygula():
            try:
                x = int(x_ofset.get())
                y = int(y_ofset.get())

                def islem(goruntu):
                    # Görüntüyü taşı
                    width, height = goruntu.size
                    yeni_goruntu = Image.new('RGB', (width, height), (255, 255, 255))
                    yeni_goruntu.paste(goruntu, (x, y))
                    return yeni_goruntu

                self.goruntu_islem_uygula(islem)
                tasima_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz ofset değerleri. Lütfen sayı girin.")

        buton_frame = tk.Frame(tasima_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=tasima_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=tasima_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def egme_dialog(self):
        """Eğme (Shearing) işlemi için dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        egme_pencere = tk.Toplevel(self.root)
        egme_pencere.title("Eğme (Shearing)")
        egme_pencere.geometry("350x200")
        egme_pencere.resizable(False, False)

        # X ve Y eğme değerleri için giriş alanları
        egme_frame = tk.Frame(egme_pencere)
        egme_frame.pack(pady=20)

        tk.Label(egme_frame, text="X Eğme (0-1):").grid(row=0, column=0, padx=10, pady=5)
        x_egme = tk.StringVar(value="0.3")
        tk.Entry(egme_frame, textvariable=x_egme, width=10).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(egme_frame, text="Y Eğme (0-1):").grid(row=1, column=0, padx=10, pady=5)
        y_egme = tk.StringVar(value="0.0")
        tk.Entry(egme_frame, textvariable=y_egme, width=10).grid(row=1, column=1, padx=10, pady=5)

        # Uygula butonu
        def egme_uygula():
            try:
                x = float(x_egme.get())
                y = float(y_egme.get())

                def islem(goruntu):
                    # Görüntüyü eğmek için PIL transform kullan
                    width, height = goruntu.size
                    yeni_genislik = int(width + abs(x) * height)
                    yeni_yukseklik = int(height + abs(y) * width)

                    # Yeni görüntü oluştur
                    egme_goruntu = goruntu.transform(
                        (yeni_genislik, yeni_yukseklik),
                        Image.AFFINE,
                        (1, x, 0, y, 1, 0),
                        resample=Image.BICUBIC
                    )
                    return egme_goruntu

                self.goruntu_islem_uygula(islem)
                egme_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz eğme değerleri. Lütfen sayı girin.")

        buton_frame = tk.Frame(egme_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=egme_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=egme_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def olcekleme_dialog(self):
        """Ölçekleme (Zoom In/Out) işlemi için dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        olcekleme_pencere = tk.Toplevel(self.root)
        olcekleme_pencere.title("Ölçekleme")
        olcekleme_pencere.geometry("350x150")
        olcekleme_pencere.resizable(False, False)

        # Ölçek faktörü için giriş alanı
        olcek_frame = tk.Frame(olcekleme_pencere)
        olcek_frame.pack(pady=20)

        tk.Label(olcek_frame, text="Ölçek Faktörü:").grid(row=0, column=0, padx=10, pady=5)
        olcek = tk.StringVar(value="1.5")
        tk.Entry(olcek_frame, textvariable=olcek, width=10).grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def olcekleme_uygula():
            try:
                faktor = float(olcek.get())

                def islem(goruntu):
                    # Görüntüyü ölçekle
                    width, height = goruntu.size
                    yeni_genislik = int(width * faktor)
                    yeni_yukseklik = int(height * faktor)
                    return goruntu.resize((yeni_genislik, yeni_yukseklik), Image.LANCZOS)

                self.goruntu_islem_uygula(islem)
                self.olcekleme_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz ölçek faktörü. Lütfen sayı girin.")

        buton_frame = tk.Frame(self.olcekleme_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=olcekleme_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.olcekleme_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def kirpma_dialog(self):
        """Kırpma işlemi için dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        kirpma_pencere = tk.Toplevel(self.root)
        kirpma_pencere.title("Kırpma")
        kirpma_pencere.geometry("400x250")
        kirpma_pencere.resizable(False, False)

        # Koordinat değerleri için giriş alanları
        width, height = self.guncel_goruntu.size

        kirpma_frame = tk.Frame(kirpma_pencere)
        kirpma_frame.pack(pady=20)

        tk.Label(kirpma_frame, text=f"Sol (0-{width}):").grid(row=0, column=0, padx=10, pady=5)
        sol = tk.StringVar(value="50")
        tk.Entry(kirpma_frame, textvariable=sol, width=10).grid(row=0, column=1, padx=10, pady=5)

        tk.Label(kirpma_frame, text=f"Üst (0-{height}):").grid(row=1, column=0, padx=10, pady=5)
        ust = tk.StringVar(value="50")
        tk.Entry(kirpma_frame, textvariable=ust, width=10).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(kirpma_frame, text=f"Sağ (0-{width}):").grid(row=2, column=0, padx=10, pady=5)
        sag = tk.StringVar(value=str(width - 50))
        tk.Entry(kirpma_frame, textvariable=sag, width=10).grid(row=2, column=1, padx=10, pady=5)

        tk.Label(kirpma_frame, text=f"Alt (0-{height}):").grid(row=3, column=0, padx=10, pady=5)
        alt = tk.StringVar(value=str(height - 50))
        tk.Entry(kirpma_frame, textvariable=alt, width=10).grid(row=3, column=1, padx=10, pady=5)

        # Uygula butonu
        def kirpma_uygula():
            try:
                l = int(sol.get())
                u = int(ust.get())
                r = int(sag.get())
                a = int(alt.get())

                if l >= r or u >= a or l < 0 or u < 0 or r > width or a > height:
                    messagebox.showerror("Hata", "Geçersiz kırpma koordinatları.")
                    return

                def islem(goruntu):
                    # Görüntüyü kırp
                    return goruntu.crop((l, u, r, a))

                self.goruntu_islem_uygula(islem)
                kirpma_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz koordinat değerleri. Lütfen sayı girin.")

        buton_frame = tk.Frame(kirpma_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=kirpma_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=kirpma_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # ----------------- Perspektif Düzeltme -----------------

    def perspektif_duzeltme_baslat(self):
        """Perspektif düzeltme modunu başlatır"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Mevcut noktaları temizle
        self.perspektif_noktalar = []
        self.perspektif_mod = True

        # Kullanıcıya talimat ver
        messagebox.showinfo("Perspektif Düzeltme",
                            "Lütfen görüntü üzerinde düzeltilmesini istediğiniz 4 noktayı seçin. "
                            "Noktaları sol üst, sağ üst, sol alt, sağ alt sırasıyla seçin.")

        self.durum_cubugu.config(text="Perspektif düzeltme modu: 4 nokta seçin")

    def perspektif_nokta_ekle(self, event):
        """Perspektif düzeltme için tıklanan noktaları işler"""
        if not self.perspektif_mod or len(self.perspektif_noktalar) >= 4:
            return

        # Tıklanan koordinatları kaydet
        x, y = event.x, event.y
        self.perspektif_noktalar.append((x, y))

        # Geçici olarak noktaları göster
        goruntu_kopya = self.guncel_goruntu.copy()
        draw = ImageDraw.Draw(goruntu_kopya)
        for nokta in self.perspektif_noktalar:
            draw.ellipse((nokta[0] - 5, nokta[1] - 5, nokta[0] + 5, nokta[1] + 5), fill="red")

        # Geçici görüntüyü göster
        self.tk_guncel_goruntu = ImageTk.PhotoImage(goruntu_kopya)
        self.islem_goruntu_alani.config(image=self.tk_guncel_goruntu)
        self.islem_goruntu_alani.image = self.tk_guncel_goruntu

        # 4 nokta seçildiyse perspektif düzeltme işlemine geç
        if len(self.perspektif_noktalar) == 4:
            self.perspektif_mod = False
            self.perspektif_duzeltme_uygula()

    def perspektif_duzeltme_uygula(self):
        """4 nokta kullanarak perspektif düzeltme uygular"""
        if len(self.perspektif_noktalar) != 4:
            return

        try:
            # OpenCV için görüntüyü dönüştür
            pil_img = self.guncel_goruntu.copy()
            cv_img = np.array(pil_img)
            cv_img = cv_img[:, :, ::-1].copy()  # RGB -> BGR

            # Kaynak noktalar (seçilen noktalar)
            pts1 = np.float32(self.perspektif_noktalar)

            # Hedef noktalar (düzeltilmiş dörtgen)
            width = max(
                np.linalg.norm(pts1[1] - pts1[0]),  # üst kenar
                np.linalg.norm(pts1[3] - pts1[2])  # alt kenar
            )

            height = max(
                np.linalg.norm(pts1[2] - pts1[0]),  # sol kenar
                np.linalg.norm(pts1[3] - pts1[1])  # sağ kenar
            )

            width, height = int(width), int(height)

            pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])

            # Perspektif dönüşüm matrisi
            M = cv2.getPerspectiveTransform(pts1, pts2)

            # Perspektif dönüşüm uygula
            dst = cv2.warpPerspective(cv_img, M, (width, height))

            # OpenCV -> PIL dönüşümü
            dst = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
            duzeltilmis_goruntu = Image.fromarray(dst)

            # Görüntüyü güncelle
            self.guncel_goruntu = duzeltilmis_goruntu
            self.tk_guncel_goruntu = self.goruntu_formatla(self.guncel_goruntu, self.islem_goruntu_alani)
            self.islem_goruntu_alani.config(image=self.tk_guncel_goruntu)
            self.islem_goruntu_alani.image = self.tk_guncel_goruntu

            self.son_islem = "perspektif_duzeltme"
            self.durum_cubugu.config(text="Perspektif düzeltme uygulandı")
        except Exception as e:
            messagebox.showerror("Hata", f"Perspektif düzeltme sırasında hata oluştu: {str(e)}")

    # Uzamsal filtreler
    def ortalama_filtre_dialog(self):
        """Ortalama filtre boyutu seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Ortalama Filtre")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Filtre boyutu seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Filtre Boyutu:").grid(row=0, column=0, padx=10, pady=5)
        boyut_var = tk.StringVar(value="3")
        boyut_combo = ttk.Combobox(filtre_frame, textvariable=boyut_var, values=["3", "5", "7", "9"], width=5)
        boyut_combo.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def ortalama_filtre_uygula():
            try:
                boyut = int(boyut_var.get())

                def islem(goruntu):
                    # PIL'in ImageFilter modülü ile ortalama filtre uygula
                    return goruntu.filter(ImageFilter.BoxBlur(boyut // 2))

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz filtre boyutu")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=ortalama_filtre_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def medyan_filtre_dialog(self):
        """Medyan filtre boyutu seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Medyan Filtre")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Filtre boyutu seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Filtre Boyutu:").grid(row=0, column=0, padx=10, pady=5)
        boyut_var = tk.StringVar(value="3")
        boyut_combo = ttk.Combobox(filtre_frame, textvariable=boyut_var, values=["3", "5", "7", "9"], width=5)
        boyut_combo.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def medyan_filtre_uygula():
            try:
                boyut = int(boyut_var.get())

                def islem(goruntu):
                    # PIL'in ImageFilter modülü ile medyan filtre uygula
                    return goruntu.filter(ImageFilter.MedianFilter(size=boyut))

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz filtre boyutu")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=medyan_filtre_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def gauss_filtre_dialog(self):
        """Gauss filtresi için radius seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Gauss Filtresi")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Radius seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Radius:").grid(row=0, column=0, padx=10, pady=5)
        radius_var = tk.StringVar(value="2")
        radius_entry = ttk.Entry(filtre_frame, textvariable=radius_var, width=5)
        radius_entry.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def gauss_filtre_uygula():
            try:
                radius = float(radius_var.get())

                def islem(goruntu):
                    # PIL'in ImageFilter modülü ile Gauss filtresi uygula
                    return goruntu.filter(ImageFilter.GaussianBlur(radius=radius))

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz radius değeri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=gauss_filtre_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def konservatif_filtre(self):
        """Konservatif filtreleme uygular"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        def islem(goruntu):
            # NumPy dizisine dönüştür
            img_array = np.array(goruntu)
            result = np.copy(img_array)

            # Her kanal için ayrı işle
            for c in range(3):  # RGB için 3 kanal
                padded = np.pad(img_array[:, :, c], 1, mode='edge')
                for i in range(1, padded.shape[0] - 1):
                    for j in range(1, padded.shape[1] - 1):
                        window = padded[i - 1:i + 2, j - 1:j + 2].flatten()
                        result[i - 1, j - 1, c] = np.min(window) if window[4] < np.min(window) else (
                            np.max(window) if window[4] > np.max(window) else window[4])

            # PIL Image'e geri dönüştür
            return Image.fromarray(result.astype(np.uint8))

        self.goruntu_islem_uygula(islem)

    def crimmins_speckle(self):
        """Crimmins speckle gürültü azaltma filtresi uygular"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        def islem(goruntu):
            # Görüntüyü OpenCV formatına dönüştür
            img = np.array(goruntu)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Crimmins algoritması için yardımcı fonksiyon
            def crimmins_iter(img_channel):
                copy = img_channel.copy()

                # N-S Pass
                for i in range(1, img_channel.shape[0] - 1):
                    for j in range(img_channel.shape[1]):
                        if copy[i - 1, j] >= copy[i, j] + 2:
                            img_channel[i, j] += 1
                        if copy[i + 1, j] >= copy[i, j] + 2:
                            img_channel[i, j] += 1

                # E-W Pass
                for i in range(img_channel.shape[0]):
                    for j in range(1, img_channel.shape[1] - 1):
                        if copy[i, j - 1] >= copy[i, j] + 2:
                            img_channel[i, j] += 1
                        if copy[i, j + 1] >= copy[i, j] + 2:
                            img_channel[i, j] += 1

                return img_channel

            # Her kanal için Crimmins algoritması uygula
            for i in range(3):  # BGR kanallları için
                for _ in range(2):  # İterasyon sayısı
                    img[:, :, i] = crimmins_iter(img[:, :, i])

            # PIL Image'e geri dönüştür
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return Image.fromarray(img)

        self.goruntu_islem_uygula(islem)

    # Frekans filtreleri
    def fourier_lpf_dialog(self):
        """Fourier alçak geçiren filtre için cutoff seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Fourier LPF")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Cutoff seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Cutoff Frekans:").grid(row=0, column=0, padx=10, pady=5)
        cutoff_var = tk.StringVar(value="30")
        cutoff_entry = ttk.Entry(filtre_frame, textvariable=cutoff_var, width=5)
        cutoff_entry.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def fourier_lpf_uygula():
            try:
                cutoff = int(cutoff_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Alçak geçiren filtre maskesi oluştur
                    mask = np.zeros((rows, cols), np.uint8)
                    mask[crow - cutoff:crow + cutoff, ccol - cutoff:ccol + cutoff] = 1

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz cutoff değeri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=fourier_lpf_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def fourier_hpf_dialog(self):
        """Fourier yüksek geçiren filtre için cutoff seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Fourier HPF")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Cutoff seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Cutoff Frekans:").grid(row=0, column=0, padx=10, pady=5)
        cutoff_var = tk.StringVar(value="30")
        cutoff_entry = ttk.Entry(filtre_frame, textvariable=cutoff_var, width=5)
        cutoff_entry.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def fourier_hpf_uygula():
            try:
                cutoff = int(cutoff_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Yüksek geçiren filtre maskesi oluştur
                    mask = np.ones((rows, cols), np.uint8)
                    mask[crow - cutoff:crow + cutoff, ccol - cutoff:ccol + cutoff] = 0

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz cutoff değeri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=fourier_hpf_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def band_geciren_dialog(self):
        """Band geçiren filtre için iç ve dış yarıçap seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Band Geçiren Filtre")
        self.filtre_pencere.geometry("350x180")
        self.filtre_pencere.resizable(False, False)

        # Yarıçap seçimleri
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="İç Yarıçap:").grid(row=0, column=0, padx=10, pady=5)
        ic_yaricap_var = tk.StringVar(value="10")
        ic_yaricap_entry = ttk.Entry(filtre_frame, textvariable=ic_yaricap_var, width=5)
        ic_yaricap_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(filtre_frame, text="Dış Yarıçap:").grid(row=1, column=0, padx=10, pady=5)
        dis_yaricap_var = tk.StringVar(value="40")
        dis_yaricap_entry = ttk.Entry(filtre_frame, textvariable=dis_yaricap_var, width=5)
        dis_yaricap_entry.grid(row=1, column=1, padx=10, pady=5)

        # Uygula butonu
        def band_geciren_uygula():
            try:
                ic_yaricap = int(ic_yaricap_var.get())
                dis_yaricap = int(dis_yaricap_var.get())

                if ic_yaricap >= dis_yaricap:
                    messagebox.showerror("Hata", "İç yarıçap dış yarıçaptan küçük olmalıdır.")
                    return

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Band geçiren filtre maskesi oluştur
                    mask = np.zeros((rows, cols), np.uint8)
                    y, x = np.ogrid[:rows, :cols]
                    mesafe_kare = (y - crow) ** 2 + (x - ccol) ** 2

                    # Halka şekilli maske
                    band = (mesafe_kare >= ic_yaricap ** 2) & (mesafe_kare <= dis_yaricap ** 2)
                    mask[band] = 1

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz yarıçap değerleri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=band_geciren_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def band_durduran_dialog(self):
        """Band durduran filtre için iç ve dış yarıçap seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Band Durduran Filtre")
        self.filtre_pencere.geometry("350x180")
        self.filtre_pencere.resizable(False, False)

        # Yarıçap seçimleri
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="İç Yarıçap:").grid(row=0, column=0, padx=10, pady=5)
        ic_yaricap_var = tk.StringVar(value="10")
        ic_yaricap_entry = ttk.Entry(filtre_frame, textvariable=ic_yaricap_var, width=5)
        ic_yaricap_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(filtre_frame, text="Dış Yarıçap:").grid(row=1, column=0, padx=10, pady=5)
        dis_yaricap_var = tk.StringVar(value="40")
        dis_yaricap_entry = ttk.Entry(filtre_frame, textvariable=dis_yaricap_var, width=5)
        dis_yaricap_entry.grid(row=1, column=1, padx=10, pady=5)

        # Uygula butonu
        def band_durduran_uygula():
            try:
                ic_yaricap = int(ic_yaricap_var.get())
                dis_yaricap = int(dis_yaricap_var.get())

                if ic_yaricap >= dis_yaricap:
                    messagebox.showerror("Hata", "İç yarıçap dış yarıçaptan küçük olmalıdır.")
                    return

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Band durduran filtre maskesi oluştur
                    mask = np.ones((rows, cols), np.uint8)
                    y, x = np.ogrid[:rows, :cols]
                    mesafe_kare = (y - crow) ** 2 + (x - ccol) ** 2

                    # Halka şekilli maskenin tersini al
                    band = (mesafe_kare >= ic_yaricap ** 2) & (mesafe_kare <= dis_yaricap ** 2)
                    mask[band] = 0

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz yarıçap değerleri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=band_durduran_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def butterworth_lpf_dialog(self):
        """Butterworth alçak geçiren filtre için cutoff ve order seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Butterworth LPF")
        self.filtre_pencere.geometry("350x180")
        self.filtre_pencere.resizable(False, False)

        # Parametre seçimleri
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Cutoff Frekans:").grid(row=0, column=0, padx=10, pady=5)
        cutoff_var = tk.StringVar(value="30")
        cutoff_entry = ttk.Entry(filtre_frame, textvariable=cutoff_var, width=5)
        cutoff_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(filtre_frame, text="Order:").grid(row=1, column=0, padx=10, pady=5)
        order_var = tk.StringVar(value="2")
        order_entry = ttk.Entry(filtre_frame, textvariable=order_var, width=5)
        order_entry.grid(row=1, column=1, padx=10, pady=5)

        # Uygula butonu
        def butterworth_lpf_uygula():
            try:
                cutoff = int(cutoff_var.get())
                order = int(order_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Butterworth alçak geçiren filtre maskesi oluştur
                    y, x = np.ogrid[:rows, :cols]
                    mesafe = np.sqrt((y - crow) ** 2 + (x - ccol) ** 2)
                    mask = 1 / (1 + (mesafe / cutoff) ** (2 * order))

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=butterworth_lpf_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def butterworth_hpf_dialog(self):
        """Butterworth yüksek geçiren filtre için cutoff ve order seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Butterworth HPF")
        self.filtre_pencere.geometry("350x180")
        self.filtre_pencere.resizable(False, False)

        # Parametre seçimleri
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Cutoff Frekans:").grid(row=0, column=0, padx=10, pady=5)
        cutoff_var = tk.StringVar(value="30")
        cutoff_entry = ttk.Entry(filtre_frame, textvariable=cutoff_var, width=5)
        cutoff_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(filtre_frame, text="Order:").grid(row=1, column=0, padx=10, pady=5)
        order_var = tk.StringVar(value="2")
        order_entry = ttk.Entry(filtre_frame, textvariable=order_var, width=5)
        order_entry.grid(row=1, column=1, padx=10, pady=5)

        # Uygula butonu
        def butterworth_hpf_uygula():
            try:
                cutoff = int(cutoff_var.get())
                order = int(order_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Butterworth yüksek geçiren filtre maskesi oluştur
                    y, x = np.ogrid[:rows, :cols]
                    mesafe = np.sqrt((y - crow) ** 2 + (x - ccol) ** 2)
                    mask = 1 / (1 + (cutoff / (mesafe + 0.000001)) ** (
                                2 * order))  # Sıfıra bölme hatası engellemek için epsilon ekle

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=butterworth_hpf_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def gaussian_lpf_dialog(self):
        """Gaussian alçak geçiren filtre için sigma seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Gaussian LPF")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Sigma seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Sigma:").grid(row=0, column=0, padx=10, pady=5)
        sigma_var = tk.StringVar(value="30")
        sigma_entry = ttk.Entry(filtre_frame, textvariable=sigma_var, width=5)
        sigma_entry.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def gaussian_lpf_uygula():
            try:
                sigma = float(sigma_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Gaussian alçak geçiren filtre maskesi oluştur
                    y, x = np.ogrid[:rows, :cols]
                    mesafe_kare = (y - crow) ** 2 + (x - ccol) ** 2
                    mask = np.exp(-mesafe_kare / (2 * sigma ** 2))

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz sigma değeri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=gaussian_lpf_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def gaussian_hpf_dialog(self):
        """Gaussian yüksek geçiren filtre için sigma seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Gaussian HPF")
        self.filtre_pencere.geometry("300x150")
        self.filtre_pencere.resizable(False, False)

        # Sigma seçimi
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Sigma:").grid(row=0, column=0, padx=10, pady=5)
        sigma_var = tk.StringVar(value="30")
        sigma_entry = ttk.Entry(filtre_frame, textvariable=sigma_var, width=5)
        sigma_entry.grid(row=0, column=1, padx=10, pady=5)

        # Uygula butonu
        def gaussian_hpf_uygula():
            try:
                sigma = float(sigma_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray)

                    # FFT uygula
                    f = np.fft.fft2(img_array)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Gaussian yüksek geçiren filtre maskesi oluştur
                    y, x = np.ogrid[:rows, :cols]
                    mesafe_kare = (y - crow) ** 2 + (x - ccol) ** 2
                    mask = 1 - np.exp(-mesafe_kare / (2 * sigma ** 2))

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Normalize et
                    img_back = (img_back - np.min(img_back)) / (np.max(img_back) - np.min(img_back)) * 255
                    img_result = Image.fromarray(img_back.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz sigma değeri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=gaussian_hpf_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def homomorfik_filtre_dialog(self):
        """Homomorfik filtre için parametre seçme dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return

        # Dialog penceresi
        self.filtre_pencere = tk.Toplevel(self.root)
        self.filtre_pencere.title("Homomorfik Filtre")
        self.filtre_pencere.geometry("350x220")
        self.filtre_pencere.resizable(False, False)

        # Parametre seçimleri
        filtre_frame = tk.Frame(self.filtre_pencere)
        filtre_frame.pack(pady=20)

        tk.Label(filtre_frame, text="Yüksek Frekans Kazancı (γH):").grid(row=0, column=0, padx=10, pady=5)
        gamma_h_var = tk.StringVar(value="2.0")
        gamma_h_entry = ttk.Entry(filtre_frame, textvariable=gamma_h_var, width=5)
        gamma_h_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(filtre_frame, text="Alçak Frekans Kazancı (γL):").grid(row=1, column=0, padx=10, pady=5)
        gamma_l_var = tk.StringVar(value="0.5")
        gamma_l_entry = ttk.Entry(filtre_frame, textvariable=gamma_l_var, width=5)
        gamma_l_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(filtre_frame, text="Cutoff Frekans:").grid(row=2, column=0, padx=10, pady=5)
        cutoff_var = tk.StringVar(value="30")
        cutoff_entry = ttk.Entry(filtre_frame, textvariable=cutoff_var, width=5)
        cutoff_entry.grid(row=2, column=1, padx=10, pady=5)

        # Uygula butonu
        def homomorfik_filtre_uygula():
            try:
                gamma_h = float(gamma_h_var.get())
                gamma_l = float(gamma_l_var.get())
                cutoff = float(cutoff_var.get())

                def islem(goruntu):
                    # Görüntüyü gri tonlamaya çevirip NumPy dizisine dönüştür
                    img_gray = goruntu.convert('L')
                    img_array = np.array(img_gray, dtype=np.float64)

                    # Log dönüşümü uygula
                    # Sıfır değerleri için küçük bir epsilon ekle
                    img_log = np.log1p(img_array)

                    # FFT uygula
                    f = np.fft.fft2(img_log)
                    fshift = np.fft.fftshift(f)

                    # Görüntü merkezini bul
                    rows, cols = img_array.shape
                    crow, ccol = rows // 2, cols // 2

                    # Homomorfik filtre maskesi oluştur
                    y, x = np.ogrid[:rows, :cols]
                    mesafe_kare = (y - crow) ** 2 + (x - ccol) ** 2
                    # Butterworth filtre bileşeni
                    mask = 1 - np.exp(-mesafe_kare / (2 * cutoff ** 2))
                    # Homomorfik filtre - yüksek ve alçak frekans kazançları
                    mask = (gamma_h - gamma_l) * mask + gamma_l

                    # Maskeleme uygula
                    fshift_filtered = fshift * mask
                    f_ishift = np.fft.ifftshift(fshift_filtered)
                    img_back = np.fft.ifft2(f_ishift)
                    img_back = np.abs(img_back)

                    # Exp dönüşümü uygula
                    img_exp = np.expm1(img_back)

                    # Normalize et
                    img_exp = (img_exp - np.min(img_exp)) / (np.max(img_exp) - np.min(img_exp)) * 255
                    img_result = Image.fromarray(img_exp.astype(np.uint8))

                    # RGB formatına dönüştür
                    return img_result.convert('RGB')

                self.goruntu_islem_uygula(islem)
                self.filtre_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")

        buton_frame = tk.Frame(self.filtre_pencere)
        buton_frame.pack(pady=10)

        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=homomorfik_filtre_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)

        iptal_btn = ttk.Button(buton_frame, text="İptal", command=self.filtre_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # SOBEL KENAR ALGILAMA
    def sobel_kenar_algilama(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        def islem(goruntu):
            cv_img = np.array(goruntu.convert('L'))
            sobel_x = cv2.Sobel(cv_img, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(cv_img, cv2.CV_64F, 0, 1, ksize=3)
            sobel_combined = np.sqrt(sobel_x**2 + sobel_y**2)
            sobel_combined = np.uint8(255 * sobel_combined / sobel_combined.max())
            return Image.fromarray(sobel_combined).convert('RGB')
        
        self.goruntu_islem_uygula(islem)

        # PREWITT KENAR ALGILAMA
    def prewitt_kenar_algilama(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        def islem(goruntu):
            cv_img = np.array(goruntu.convert('L'))
            kernelx = np.array([[-1,0,1],[-1,0,1],[-1,0,1]], np.float32)
            kernely = np.array([[-1,-1,-1],[0,0,0],[1,1,1]], np.float32)
            prewitt_x = cv2.filter2D(cv_img, -1, kernelx)
            prewitt_y = cv2.filter2D(cv_img, -1, kernely)
            prewitt_combined = np.sqrt(prewitt_x**2 + prewitt_y**2)
            prewitt_combined = np.uint8(255 * prewitt_combined / prewitt_combined.max())
            return Image.fromarray(prewitt_combined).convert('RGB')
        
        self.goruntu_islem_uygula(islem)

        # ROBERTS CROSS KENAR ALGILAMA
    def roberts_cross_algilama(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        def islem(goruntu):
            cv_img = np.array(goruntu.convert('L'))
            kernelx = np.array([[1,0],[0,-1]], np.float32)
            kernely = np.array([[0,1],[-1,0]], np.float32)
            roberts_x = cv2.filter2D(cv_img, -1, kernelx)
            roberts_y = cv2.filter2D(cv_img, -1, kernely)
            roberts_combined = np.sqrt(roberts_x**2 + roberts_y**2)
            roberts_combined = np.uint8(255 * roberts_combined / roberts_combined.max())
            return Image.fromarray(roberts_combined).convert('RGB')
        
        self.goruntu_islem_uygula(islem)

        # COMPASS KENAR ALGILAMA
    def compass_kenar_algilama(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        def islem(goruntu):
            cv_img = np.array(goruntu.convert('L'))
            kernels = [
                np.array([[-1,-1,-1],[1,1,1],[1,1,1]], np.float32),  # Doğu
                np.array([[1,1,1],[1,1,1],[-1,-1,-1]], np.float32),  # Batı
                np.array([[-1,1,1],[-1,1,1],[-1,1,1]], np.float32),  # Kuzey
                np.array([[1,1,-1],[1,1,-1],[1,1,-1]], np.float32),  # Güney
                np.array([[-1,-1,1],[-1,1,1],[-1,1,1]], np.float32),  # KD
                np.array([[1,1,1],[-1,1,1],[-1,-1,1]], np.float32),  # GD
                np.array([[1,-1,-1],[1,1,-1],[1,1,-1]], np.float32),  # KB
                np.array([[1,1,1],[1,1,-1],[1,-1,-1]], np.float32)   # GB
            ]
            
            max_response = np.zeros_like(cv_img, dtype=np.float64)
            for kernel in kernels:
                response = cv2.filter2D(cv_img, -1, kernel)
                max_response = np.maximum(max_response, np.abs(response))
            
            max_response = np.uint8(255 * max_response / max_response.max())
            return Image.fromarray(max_response).convert('RGB')
        
        self.goruntu_islem_uygula(islem)

        # CANNY KENAR ALGILAMA DIALOG
    def canny_kenar_dialog(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        canny_pencere = tk.Toplevel(self.root)
        canny_pencere.title("Canny Kenar Algılama")
        canny_pencere.geometry("350x180")
        canny_pencere.resizable(False, False)
        
        # Parametreler
        threshold_frame = tk.Frame(canny_pencere)
        threshold_frame.pack(pady=20)
        
        tk.Label(threshold_frame, text="Alt Eşik:").grid(row=0, column=0, padx=10, pady=5)
        alt_esik_var = tk.StringVar(value="50")
        tk.Entry(threshold_frame, textvariable=alt_esik_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(threshold_frame, text="Üst Eşik:").grid(row=1, column=0, padx=10, pady=5)
        ust_esik_var = tk.StringVar(value="150")
        tk.Entry(threshold_frame, textvariable=ust_esik_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        def canny_uygula():
            try:
                alt_esik = int(alt_esik_var.get())
                ust_esik = int(ust_esik_var.get())
                
                def islem(goruntu):
                    cv_img = np.array(goruntu.convert('L'))
                    canny_edges = cv2.Canny(cv_img, alt_esik, ust_esik)
                    return Image.fromarray(canny_edges).convert('RGB')
                
                self.goruntu_islem_uygula(islem)
                canny_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz eşik değerleri")
        
        buton_frame = tk.Frame(canny_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=canny_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=canny_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # LAPLACE KENAR ALGILAMA
    def laplace_kenar_algilama(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        def islem(goruntu):
            cv_img = np.array(goruntu.convert('L'))
            laplace = cv2.Laplacian(cv_img, cv2.CV_64F)
            laplace = np.uint8(np.absolute(laplace))
            return Image.fromarray(laplace).convert('RGB')
        
        self.goruntu_islem_uygula(islem)

        # GABOR FİLTRE DIALOG
    def gabor_filtre_dialog(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        gabor_pencere = tk.Toplevel(self.root)
        gabor_pencere.title("Gabor Filtresi")
        gabor_pencere.geometry("350x250")
        gabor_pencere.resizable(False, False)
        
        # Parametreler
        param_frame = tk.Frame(gabor_pencere)
        param_frame.pack(pady=20)
        
        tk.Label(param_frame, text="Lambda:").grid(row=0, column=0, padx=10, pady=5)
        lambda_var = tk.StringVar(value="10")
        tk.Entry(param_frame, textvariable=lambda_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Theta (derece):").grid(row=1, column=0, padx=10, pady=5)
        theta_var = tk.StringVar(value="0")
        tk.Entry(param_frame, textvariable=theta_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Sigma:").grid(row=2, column=0, padx=10, pady=5)
        sigma_var = tk.StringVar(value="4")
        tk.Entry(param_frame, textvariable=sigma_var, width=10).grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Gamma:").grid(row=3, column=0, padx=10, pady=5)
        gamma_var = tk.StringVar(value="0.5")
        tk.Entry(param_frame, textvariable=gamma_var, width=10).grid(row=3, column=1, padx=10, pady=5)
        
        def gabor_uygula():
            try:
                lambda_val = float(lambda_var.get())
                theta_val = float(theta_var.get()) * np.pi / 180  # Convert to radians
                sigma_val = float(sigma_var.get())
                gamma_val = float(gamma_var.get())
                
                def islem(goruntu):
                    cv_img = np.array(goruntu.convert('L'))
                    kernel = cv2.getGaborKernel((21, 21), sigma_val, theta_val, lambda_val, gamma_val, 0, ktype=cv2.CV_32F)
                    filtered_img = cv2.filter2D(cv_img, cv2.CV_8UC3, kernel)
                    return Image.fromarray(filtered_img).convert('RGB')
                
                self.goruntu_islem_uygula(islem)
                gabor_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")
        
        buton_frame = tk.Frame(gabor_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=gabor_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=gabor_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # HOUGH DOĞRU DIALOG
    def hough_line_dialog(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        hough_pencere = tk.Toplevel(self.root)
        hough_pencere.title("Hough Doğru Tespiti")
        hough_pencere.geometry("350x180")
        hough_pencere.resizable(False, False)
        
        # Parametreler
        param_frame = tk.Frame(hough_pencere)
        param_frame.pack(pady=20)
        
        tk.Label(param_frame, text="Threshold:").grid(row=0, column=0, padx=10, pady=5)
        threshold_var = tk.StringVar(value="100")
        tk.Entry(param_frame, textvariable=threshold_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Min Line Length:").grid(row=1, column=0, padx=10, pady=5)
        minlinelength_var = tk.StringVar(value="50")
        tk.Entry(param_frame, textvariable=minlinelength_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        def hough_line_uygula():
            try:
                threshold = int(threshold_var.get())
                minlinelength = int(minlinelength_var.get())
                
                def islem(goruntu):
                    cv_img = np.array(goruntu.convert('L'))
                    edges = cv2.Canny(cv_img, 50, 150)
                    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold, minLineLength=minlinelength, maxLineGap=10)
                    
                    line_image = np.copy(goruntu)
                    line_image = np.array(line_image)
                    
                    if lines is not None:
                        for line in lines:
                            x1, y1, x2, y2 = line[0]
                            cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    
                    return Image.fromarray(line_image)
                
                self.goruntu_islem_uygula(islem)
                hough_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")
        
        buton_frame = tk.Frame(hough_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=hough_line_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=hough_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # HOUGH ÇEMBER DIALOG
    def hough_circle_dialog(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        hough_pencere = tk.Toplevel(self.root)
        hough_pencere.title("Hough Çember Tespiti")
        hough_pencere.geometry("350x220")
        hough_pencere.resizable(False, False)
        
        # Parametreler
        param_frame = tk.Frame(hough_pencere)
        param_frame.pack(pady=20)
        
        tk.Label(param_frame, text="Param1:").grid(row=0, column=0, padx=10, pady=5)
        param1_var = tk.StringVar(value="100")
        tk.Entry(param_frame, textvariable=param1_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Param2:").grid(row=1, column=0, padx=10, pady=5)
        param2_var = tk.StringVar(value="30")
        tk.Entry(param_frame, textvariable=param2_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Min Radius:").grid(row=2, column=0, padx=10, pady=5)
        minradius_var = tk.StringVar(value="10")
        tk.Entry(param_frame, textvariable=minradius_var, width=10).grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(param_frame, text="Max Radius:").grid(row=3, column=0, padx=10, pady=5)
        maxradius_var = tk.StringVar(value="100")
        tk.Entry(param_frame, textvariable=maxradius_var, width=10).grid(row=3, column=1, padx=10, pady=5)
        
        def hough_circle_uygula():
            try:
                param1 = int(param1_var.get())
                param2 = int(param2_var.get())
                minradius = int(minradius_var.get())
                maxradius = int(maxradius_var.get())
                
                def islem(goruntu):
                    cv_img = np.array(goruntu.convert('L'))
                    circles = cv2.HoughCircles(cv_img, cv2.HOUGH_GRADIENT, 1, 20, 
                                            param1=param1, param2=param2, 
                                            minRadius=minradius, maxRadius=maxradius)
                    
                    circle_image = np.copy(goruntu)
                    circle_image = np.array(circle_image)
                    
                    if circles is not None:
                        circles = np.uint16(np.around(circles))
                        for i in circles[0, :]:
                            cv2.circle(circle_image, (i[0], i[1]), i[2], (0, 255, 0), 2)
                            cv2.circle(circle_image, (i[0], i[1]), 2, (0, 0, 255), 3)
                    
                    return Image.fromarray(circle_image)
                
                self.goruntu_islem_uygula(islem)
                hough_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")
        
        buton_frame = tk.Frame(hough_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=hough_circle_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=hough_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

        # K-MEANS SEGMENTASYON DIALOG
    def kmeans_segmentation_dialog(self):
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        kmeans_pencere = tk.Toplevel(self.root)
        kmeans_pencere.title("K-Means Segmentasyon")
        kmeans_pencere.geometry("350x150")
        kmeans_pencere.resizable(False, False)
        
        # Parametreler
        param_frame = tk.Frame(kmeans_pencere)
        param_frame.pack(pady=20)
        
        tk.Label(param_frame, text="Küme Sayısı (K):").grid(row=0, column=0, padx=10, pady=5)
        k_var = tk.StringVar(value="3")
        tk.Entry(param_frame, textvariable=k_var, width=10).grid(row=0, column=1, padx=10, pady=5)
        
        def kmeans_uygula():
            try:
                k = int(k_var.get())
                
                def islem(goruntu):
                    cv_img = np.array(goruntu)
                    Z = cv_img.reshape((-1, 3))
                    Z = np.float32(Z)
                    
                    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                    ret, label, center = cv2.kmeans(Z, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                    
                    center = np.uint8(center)
                    res = center[label.flatten()]
                    res2 = res.reshape((cv_img.shape))
                    
                    return Image.fromarray(res2)
                
                self.goruntu_islem_uygula(islem)
                kmeans_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz küme sayısı")
        
        buton_frame = tk.Frame(kmeans_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=kmeans_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=kmeans_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)


    def erosion_dialog(self):
        """Erosion işlemi için dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        erosion_pencere = tk.Toplevel(self.root)
        erosion_pencere.title("Erosion (Aşındırma)")
        erosion_pencere.geometry("350x200")
        erosion_pencere.resizable(False, False)
        
        # Kernel boyutu seçimi
        kernel_frame = tk.Frame(erosion_pencere)
        kernel_frame.pack(pady=20)
        
        tk.Label(kernel_frame, text="Kernel Boyutu:").grid(row=0, column=0, padx=10, pady=5)
        kernel_size_var = tk.StringVar(value="3")
        kernel_combo = ttk.Combobox(kernel_frame, textvariable=kernel_size_var, 
                                values=["3", "5", "7", "9", "11"], width=5)
        kernel_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # İterasyon sayısı
        tk.Label(kernel_frame, text="İterasyon Sayısı:").grid(row=1, column=0, padx=10, pady=5)
        iteration_var = tk.StringVar(value="1")
        iteration_entry = ttk.Entry(kernel_frame, textvariable=iteration_var, width=5)
        iteration_entry.grid(row=1, column=1, padx=10, pady=5)
        
        def erosion_uygula():
            try:
                kernel_size = int(kernel_size_var.get())
                iterations = int(iteration_var.get())
                
                def islem(goruntu):
                    # Görüntüyü NumPy array'e dönüştür
                    img_array = np.array(goruntu)
                    
                    # Eğer RGB ise her kanala ayrı işlem uygula
                    if len(img_array.shape) == 3:
                        # BGR formatına dönüştür (OpenCV için)
                        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        
                        # Kernel oluştur
                        kernel = np.ones((kernel_size, kernel_size), np.uint8)
                        
                        # Erosion uygula
                        eroded = cv2.erode(img_bgr, kernel, iterations=iterations)
                        
                        # RGB'ye geri dönüştür
                        result = cv2.cvtColor(eroded, cv2.COLOR_BGR2RGB)
                    else:
                        # Gri tonlama görüntü
                        kernel = np.ones((kernel_size, kernel_size), np.uint8)
                        result = cv2.erode(img_array, kernel, iterations=iterations)
                    
                    return Image.fromarray(result)
                
                self.goruntu_islem_uygula(islem)
                erosion_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")
        
        # Butonlar
        buton_frame = tk.Frame(erosion_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=erosion_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=erosion_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def dilation_dialog(self):
        """Dilation işlemi için dialog penceresi"""
        if self.orjinal_goruntu is None:
            messagebox.showinfo("Bilgi", "Lütfen önce bir görüntü yükleyin")
            return
        
        # Dialog penceresi
        dilation_pencere = tk.Toplevel(self.root)
        dilation_pencere.title("Dilation (Genişletme)")
        dilation_pencere.geometry("350x200")
        dilation_pencere.resizable(False, False)
        
        # Kernel boyutu seçimi
        kernel_frame = tk.Frame(dilation_pencere)
        kernel_frame.pack(pady=20)
        
        tk.Label(kernel_frame, text="Kernel Boyutu:").grid(row=0, column=0, padx=10, pady=5)
        kernel_size_var = tk.StringVar(value="3")
        kernel_combo = ttk.Combobox(kernel_frame, textvariable=kernel_size_var, 
                                values=["3", "5", "7", "9", "11"], width=5)
        kernel_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # İterasyon sayısı
        tk.Label(kernel_frame, text="İterasyon Sayısı:").grid(row=1, column=0, padx=10, pady=5)
        iteration_var = tk.StringVar(value="1")
        iteration_entry = ttk.Entry(kernel_frame, textvariable=iteration_var, width=5)
        iteration_entry.grid(row=1, column=1, padx=10, pady=5)
        
        def dilation_uygula():
            try:
                kernel_size = int(kernel_size_var.get())
                iterations = int(iteration_var.get())
                
                def islem(goruntu):
                    # Görüntüyü NumPy array'e dönüştür
                    img_array = np.array(goruntu)
                    
                    # Eğer RGB ise her kanala ayrı işlem uygula
                    if len(img_array.shape) == 3:
                        # BGR formatına dönüştür (OpenCV için)
                        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                        
                        # Kernel oluştur
                        kernel = np.ones((kernel_size, kernel_size), np.uint8)
                        
                        # Dilation uygula
                        dilated = cv2.dilate(img_bgr, kernel, iterations=iterations)
                        
                        # RGB'ye geri dönüştür
                        result = cv2.cvtColor(dilated, cv2.COLOR_BGR2RGB)
                    else:
                        # Gri tonlama görüntü
                        kernel = np.ones((kernel_size, kernel_size), np.uint8)
                        result = cv2.dilate(img_array, kernel, iterations=iterations)
                    
                    return Image.fromarray(result)
                
                self.goruntu_islem_uygula(islem)
                dilation_pencere.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz parametre değerleri")
        
        # Butonlar
        buton_frame = tk.Frame(dilation_pencere)
        buton_frame.pack(pady=10)
        
        uygula_btn = ttk.Button(buton_frame, text="Uygula", command=dilation_uygula)
        uygula_btn.pack(side=tk.LEFT, padx=10)
        
        iptal_btn = ttk.Button(buton_frame, text="İptal", command=dilation_pencere.destroy)
        iptal_btn.pack(side=tk.LEFT, padx=10)

    def hakkinda_goster(self):
        messagebox.showinfo(
            "Hakkında",
            "Görüntü İşleme Uygulaması\nSürüm 1.0\n\nGörüntü İşleme Vize Ödevi için geliştirilmiştir.\nPython ve Tkinter kullanılarak oluşturulmuştur."
        )

# Ana uygulamayı başlat
if __name__ == "__main__":
    root = tk.Tk()
    uygulama = GoruntuIslemeUygulamasi(root)
    root.mainloop()