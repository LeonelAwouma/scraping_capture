# analyze_screenshots.py
import google.generativeai as genai
from pathlib import Path
import csv
import time
from PIL import Image
import json

class ScreenshotAnalyzer:
    def __init__(self, api_key):
        """Initialise l'analyseur avec l'API Gemini"""
        print("🤖 Initialisation de Gemini AI...")
        genai.configure(api_key=api_key)
        
        # Utiliser Gemini 2.0 Flash (gratuit et performant)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        print("✅ Gemini 2.0 Flash chargé!\n")
    
    def analyze_screenshot(self, image_path, page_number):
        """
        Analyse une capture d'écran et extrait les informations
        
        Args:
            image_path: Chemin vers l'image
            page_number: Numéro de la page
            
        Returns:
            dict: Informations extraites
        """
        try:
            print(f"🔍 Analyse de la page {page_number}...")
            
            # Charger l'image
            img = Image.open(image_path)
            
            # Prompt pour Gemini
            prompt = """
            Analyse cette page de catalogue d'ordinateurs portables.
            
            Pour chaque produit visible, extrais les informations suivantes en JSON :
            - title: Nom du produit
            - price: Prix (nombre uniquement, sans $)
            - description: Description technique
            - reviews: Nombre d'avis
            - rating: Note sur 5 (compte les étoiles)
            - stock_status: "En stock" ou "Rupture" ou "Inconnu"
            - promotions: Y a-t-il des promotions visibles? (oui/non)
            - visual_quality: Qualité de l'image produit (bonne/moyenne/mauvaise)
            
            Retourne UNIQUEMENT un JSON valide au format:
            {
                "page": numéro_page,
                "products": [
                    {
                        "title": "...",
                        "price": "...",
                        "description": "...",
                        "reviews": "...",
                        "rating": ...,
                        "stock_status": "...",
                        "promotions": "...",
                        "visual_quality": "..."
                    }
                ],
                "page_layout": "description du layout général",
                "total_products": nombre_de_produits
            }
            
            Si tu ne peux pas extraire une information, mets "N/A".
            """
            
            # Envoyer à Gemini
            response = self.model.generate_content([prompt, img])
            
            # Parser la réponse
            response_text = response.text.strip()
            
            # Nettoyer la réponse (enlever les balises markdown si présentes)
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            # Parser le JSON
            analysis = json.loads(response_text)
            analysis['page'] = page_number
            
            print(f"   ✅ {analysis.get('total_products', 0)} produits analysés")
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Erreur de parsing JSON: {e}")
            print(f"   Réponse brute: {response_text[:200]}...")
            return None
        except Exception as e:
            print(f"   ❌ Erreur lors de l'analyse: {str(e)[:100]}")
            return None
    
    def analyze_all_screenshots(self, screenshots_folder, output_csv="analysis_results.csv"):
        """
        Analyse toutes les captures d'écran d'un dossier
        
        Args:
            screenshots_folder: Chemin vers le dossier contenant les screenshots
            output_csv: Nom du fichier CSV de sortie
        """
        screenshots_path = Path(screenshots_folder)
        
        if not screenshots_path.exists():
            print(f"❌ Le dossier {screenshots_folder} n'existe pas!")
            return
        
        # Récupérer tous les fichiers PNG
        screenshot_files = sorted(screenshots_path.glob("page_*.png"))
        
        if not screenshot_files:
            print(f"❌ Aucune capture d'écran trouvée dans {screenshots_folder}")
            return
        
        print(f"\n{'='*70}")
        print(f"📸 {len(screenshot_files)} captures d'écran trouvées")
        print(f"🤖 Début de l'analyse avec Gemini AI")
        print(f"{'='*70}\n")
        
        all_results = []
        
        # Analyser chaque capture
        for idx, screenshot_file in enumerate(screenshot_files, 1):
            page_num = idx
            
            print(f"\n📄 PAGE {page_num}/{len(screenshot_files)}")
            print("-" * 70)
            
            analysis = self.analyze_screenshot(screenshot_file, page_num)
            
            if analysis:
                all_results.append(analysis)
                print(f"   💾 Résultats sauvegardés")
            
            # Pause pour respecter les limites de l'API
            if idx < len(screenshot_files):
                print("   ⏳ Pause de 2 secondes...")
                time.sleep(2)
        
        # Sauvegarder les résultats
        self.save_results_to_csv(all_results, output_csv)
        self.save_results_to_json(all_results, "analysis_results.json")
        
        print(f"\n{'='*70}")
        print(f"🎉 ANALYSE TERMINÉE!")
        print(f"📊 {len(all_results)} pages analysées")
        print(f"📁 Résultats CSV: {output_csv}")
        print(f"📁 Résultats JSON: analysis_results.json")
        print(f"{'='*70}\n")
    
    def save_results_to_csv(self, results, output_file):
        """Sauvegarde les résultats dans un CSV"""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # En-têtes
                writer.writerow([
                    'page', 'product_index', 'title', 'price', 'description',
                    'reviews', 'rating', 'stock_status', 'promotions', 
                    'visual_quality', 'page_layout'
                ])
                
                # Données
                for result in results:
                    page = result.get('page', 'N/A')
                    page_layout = result.get('page_layout', 'N/A')
                    
                    products = result.get('products', [])
                    for idx, product in enumerate(products, 1):
                        writer.writerow([
                            page,
                            idx,
                            product.get('title', 'N/A'),
                            product.get('price', 'N/A'),
                            product.get('description', 'N/A'),
                            product.get('reviews', 'N/A'),
                            product.get('rating', 'N/A'),
                            product.get('stock_status', 'N/A'),
                            product.get('promotions', 'N/A'),
                            product.get('visual_quality', 'N/A'),
                            page_layout
                        ])
            
            print(f"\n✅ CSV sauvegardé: {output_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde CSV: {e}")
    
    def save_results_to_json(self, results, output_file):
        """Sauvegarde les résultats en JSON (format complet)"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ JSON sauvegardé: {output_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde JSON: {e}")


def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print("🤖 ANALYSEUR DE CAPTURES D'ÉCRAN AVEC GEMINI AI")
    print("="*70 + "\n")
    
    # Configuration
    API_KEY = "AIzaSyDdNgyD5vFH1o6i-QtWcTWrmWBUpTHe5SY"
    
    # Trouver le dossier de screenshots le plus récent
    screenshots_folders = sorted(Path(".").glob("screenshots_*"), reverse=True)
    
    if not screenshots_folders:
        print("❌ Aucun dossier de screenshots trouvé!")
        print("💡 Assurez-vous d'avoir d'abord exécuté le spider de scraping")
        return
    
    screenshots_folder = screenshots_folders[0]
    print(f"📁 Dossier détecté: {screenshots_folder}")
    
    # Créer l'analyseur
    analyzer = ScreenshotAnalyzer(API_KEY)
    
    # Analyser toutes les captures
    analyzer.analyze_all_screenshots(
        screenshots_folder=screenshots_folder,
        output_csv="gemini_analysis.csv"
    )


if __name__ == "__main__":
    # Installation des dépendances
    print("📦 Vérification des dépendances...\n")
    try:
        import google.generativeai
        from PIL import Image
        print("✅ Toutes les dépendances sont installées\n")
    except ImportError as e:
        print("❌ Dépendances manquantes!")
        print("\n💡 Installez-les avec:")
        print("   pip install google-generativeai pillow")
        exit(1)
    
    main()