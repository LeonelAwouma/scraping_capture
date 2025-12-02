# ecommerce_scraper/spiders/laptops.py
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import os

class LaptopsSpider(scrapy.Spider):
    name = 'laptops'
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'HTTPCACHE_ENABLED': False,
        'FEED_EXPORT_ENCODING': 'utf-8',
        # ⭐ Désactiver le feed export par défaut (on gère manuellement)
        'FEEDS': {}
    }
    
    def __init__(self):
        print("🚀 Initialisation du spider avec Selenium...")
        
        # ⭐ Initialiser le fichier CSV dès le début
        self.csv_filename = 'laptops_progressive.csv'
        self.csv_file = None
        self.csv_writer = None
        self.init_csv()
        
        # Configuration Chrome
        chrome_options = Options()
        
        # ⭐ IMPORTANT: Spécifier le chemin de Chrome.exe
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\MARCOM\AppData\Local\Google\Chrome\Application\chrome.exe",
        ]
        
        chrome_binary = None
        import os
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"✅ Chrome trouvé à: {path}")
                break
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        else:
            print("⚠️ Chrome non trouvé aux emplacements standards")
            print("💡 Veuillez installer Chrome ou spécifier le chemin manuellement")
        
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chromedriver_path = r"C:\chromedriver\chromedriver.exe"
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(chromedriver_path),
                options=chrome_options
            )
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Driver Chrome initialisé avec succès!")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du driver: {e}")
            print("\n💡 SOLUTION:")
            print("   1. Vérifiez votre version de Chrome: chrome://version/")
            print("   2. Téléchargez ChromeDriver: https://googlechromelabs.github.io/chrome-for-testing/")
            print(f"   3. Placez chromedriver.exe à: {chromedriver_path}")
            raise
    
    def init_csv(self):
        """Initialise le fichier CSV avec les en-têtes"""
        try:
            # Supprimer le fichier s'il existe déjà
            if os.path.exists(self.csv_filename):
                os.remove(self.csv_filename)
                print(f"🗑️ Ancien fichier {self.csv_filename} supprimé")
            
            # Créer le nouveau fichier avec les en-têtes
            self.csv_file = open(self.csv_filename, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(
                self.csv_file,
                fieldnames=['page', 'title', 'price', 'description', 'reviews', 'rating', 'link']
            )
            self.csv_writer.writeheader()
            self.csv_file.flush()  # Forcer l'écriture immédiate
            print(f"✅ Fichier CSV initialisé: {self.csv_filename}\n")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du CSV: {e}")
            raise
    
    def write_to_csv(self, item):
        """Écrit un item dans le CSV immédiatement"""
        try:
            self.csv_writer.writerow(item)
            self.csv_file.flush()  # ⭐ Crucial: forcer l'écriture sur le disque
            os.fsync(self.csv_file.fileno())  # ⭐ Double sécurité
        except Exception as e:
            print(f"❌ Erreur lors de l'écriture dans le CSV: {e}")
    
    def start_requests(self):
        """Point d'entrée du spider"""
        url = "https://webscraper.io/test-sites/e-commerce/ajax/computers/laptops"
        print(f"\n{'='*70}")
        print(f"🔄 DÉBUT DU SCRAPING MULTI-PAGES")
        print(f"💾 Écriture progressive dans: {self.csv_filename}")
        print(f"{'='*70}\n")
        yield scrapy.Request(url, callback=self.parse_all_pages, dont_filter=True)
    
    def parse_all_pages(self, response):
        """Scrape toutes les pages en utilisant Selenium"""
        current_page = 1
        max_pages = 20
        total_items = 0
        
        # Charger la première page
        self.driver.get(response.url)
        print(f"📡 Navigation vers: {response.url}")
        
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbnail")))
            print("✅ Page initiale chargée avec succès!")
            time.sleep(3)
        except TimeoutException:
            print("❌ Timeout: impossible de charger la page")
            return
        
        # Boucle de scraping multi-pages
        while current_page <= max_pages:
            try:
                print(f"\n📄 PAGE {current_page}")
                print("-" * 70)
                
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbnail")))
                time.sleep(2)
                
                products = self.driver.find_elements(By.CLASS_NAME, "thumbnail")
                print(f"   🔍 {len(products)} ordinateurs trouvés")
                
                if len(products) == 0:
                    print("   ⚠️ Aucun produit - Arrêt du scraping")
                    break
                
                # Scraper chaque produit
                for idx, product in enumerate(products, 1):
                    try:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                            product
                        )
                        time.sleep(0.15)
                        
                        # Extraction des données
                        title = product.find_element(By.CLASS_NAME, "title").text.strip()
                        price_text = product.find_element(By.CLASS_NAME, "price").text
                        price = price_text.replace("$", "").replace(",", "").strip()
                        
                        try:
                            description = product.find_element(By.CLASS_NAME, "description").text.strip()
                        except NoSuchElementException:
                            description = ""
                        
                        try:
                            reviews_text = product.find_element(By.CSS_SELECTOR, ".ratings p.review-count").text.strip()
                            reviews = reviews_text.split()[0] if reviews_text else "0"
                        except NoSuchElementException:
                            reviews = "0"
                        
                        rating = self.extract_rating(product)
                        
                        try:
                            link = product.find_element(By.CLASS_NAME, "title").get_attribute("href")
                        except NoSuchElementException:
                            link = ""
                        
                        # Créer l'item
                        item = {
                            'page': current_page,
                            'title': title,
                            'price': price,
                            'description': description,
                            'reviews': reviews,
                            'rating': rating,
                            'link': link
                        }
                        
                        # ⭐ Écrire immédiatement dans le CSV
                        self.write_to_csv(item)
                        total_items += 1
                        
                        # Afficher un indicateur de progression
                        if idx % 3 == 0 or idx == len(products):
                            print(f"   💾 [{idx}/{len(products)}] items écrits dans le CSV")
                        
                        # Yield pour Scrapy (optionnel, mais conservé pour compatibilité)
                        yield item
                        
                    except Exception as e:
                        print(f"   ⚠️ Erreur produit #{idx}: {str(e)[:50]}")
                        continue
                
                print(f"   ✅ Page {current_page} scrapée: {len(products)} items | Total: {total_items}")
                
                # Navigation vers la page suivante
                if current_page < max_pages:
                    print(f"\n   🔄 Navigation vers page {current_page + 1}...")
                    
                    if not self.click_next_button():
                        print(f"\n   ℹ️ Fin de la pagination à la page {current_page}")
                        break
                    
                    current_page += 1
                    print(f"   ⏳ Chargement de la page {current_page}...")
                    time.sleep(4)
                    
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)
                    self.driver.execute_script("window.scrollTo(0, 800);")
                    time.sleep(1)
                    
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbnail")))
                        print(f"   ✅ Page {current_page} chargée!")
                    except TimeoutException:
                        print("   ⚠️ Timeout - Nouveaux produits non chargés")
                        break
                else:
                    break
                    
            except Exception as e:
                print(f"   ❌ Erreur critique sur page {current_page}: {str(e)[:100]}")
                break
        
        print(f"\n{'='*70}")
        print(f"🎉 SCRAPING TERMINÉ!")
        print(f"📄 Nombre de pages parcourues: {current_page}")
        print(f"💾 Total d'items écrits: {total_items}")
        print(f"📁 Fichier: {self.csv_filename}")
        print(f"{'='*70}\n")
    
    def extract_rating(self, product):
        """Extrait le nombre d'étoiles (rating) d'un produit"""
        try:
            rating_stars = product.find_elements(By.CSS_SELECTOR, ".ratings .ws-icon-star")
            rating = len(rating_stars)
            if rating > 0:
                return rating
        except:
            pass
        return 0
    
    def click_next_button(self):
        """Clique sur le bouton 'Next >' pour passer à la page suivante"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            
            print("   🔍 Recherche du bouton 'Next >'...")
            
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            for button in all_buttons:
                text = button.text.strip()
                
                if "next" in text.lower() or text == ">" or ">" in text:
                    print(f"      Bouton trouvé: '{text}'")
                    
                    if not button.is_enabled() or button.get_attribute("disabled"):
                        print("   🏁 Bouton désactivé - Dernière page atteinte!")
                        return False
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", button)
                    print(f"   ✅ Clic réussi sur le bouton '{text}'!")
                    return True
            
            print("   ⚠️ Aucun bouton 'Next' trouvé")
            
        except Exception as e:
            print(f"   ⚠️ Erreur lors du clic: {str(e)[:80]}")
        
        return False
    
    def closed(self, reason):
        """Fermeture propre du driver Selenium et du fichier CSV"""
        print("\n⏳ Fermeture du navigateur...")
        self.driver.quit()
        print("✅ Navigateur fermé")
        
        # ⭐ Fermer le fichier CSV proprement
        if self.csv_file:
            self.csv_file.close()
            print(f"✅ Fichier CSV fermé: {self.csv_filename}")
        
        print("✅ Spider terminé avec succès!")