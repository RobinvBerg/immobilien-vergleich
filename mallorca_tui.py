#!/usr/bin/env python3
"""
Mallorca Properties TUI - Safe interface without context overflow
Uses extracted JSON data instead of reading large HTML files
"""

import json
import os
from pathlib import Path

class MallorcaTUI:
    def __init__(self):
        self.base_path = Path(__file__).parent / "mallorca-projekt"
        self.property_names = [
            "Establiments — Das Volumen; 762m² zum Umdenken",
            "Binissalem — Platz für alle; 8 Zimmer, endlose Gärten", 
            "Establiments — Charme-Refugium; altes Steinhaus mit Charakter",
            "Palmanyola — Klein aber Wow; Designvilla vor den Toren Palmas",
            "Santa Maria — Potenzial pur; Rohling in Traumlage",
            "Campos — Zum Selbermachen; ehrliche Finca, ehrlicher Preis",
            "Sa Ràpita — Strandgold; aufwachen, Es Trenc, fertig",
            "Sa Ràpita — Vision 1800; 5 Hektar warten auf deine Handschrift",
            "Sencelles — 13 Hektar Paradies; dein eigenes Landgut",
            "Ses Salines — Neubau Deluxe; einziehen und leben",
            "Moscari — Architekten-Traum; Design trifft Serra de Tramuntana",
            "Campos — Finca mit Lizenz; 14 Hektar mallorquinischer Traum",
            "Bunyola — Berglage mit Lizenz; Tramuntana vor der Tür"
        ]
        self.load_safe_data()
    
    def load_safe_data(self):
        """Load data from small JSON files, never the huge HTML files"""
        self.excel_data = {}
        self.distances = {}
        
        try:
            # Load Excel data
            excel_path = self.base_path / "excel_data_with_links.json"
            if excel_path.exists():
                with open(excel_path, 'r', encoding='utf-8') as f:
                    self.excel_data = json.load(f)
            
            # Load distances  
            dist_path = self.base_path / "distances.json"
            if dist_path.exists():
                with open(dist_path, 'r', encoding='utf-8') as f:
                    self.distances = json.load(f)
                    
        except Exception as e:
            print(f"⚠️  Warning loading data: {e}")
    
    def show_menu(self):
        """Main menu without loading huge files"""
        print("\n🏠 Mallorca Properties TUI - Safe Mode")
        print("=" * 50)
        print("1. List all properties")
        print("2. Show property by index")
        print("3. Search properties")
        print("4. Show Excel data")
        print("5. Show distances")
        print("6. Export property names")
        print("0. Exit")
        return input("\nChoice: ").strip()
    
    def list_properties(self):
        """List all properties with indexes"""
        print("\n📋 Property List:")
        print("-" * 60)
        for i, name in enumerate(self.property_names, 1):
            print(f"{i:2d}. {name}")
    
    def show_property(self, index):
        """Show single property details"""
        try:
            idx = int(index) - 1
            if 0 <= idx < len(self.property_names):
                name = self.property_names[idx]
                print(f"\n🏡 Property #{index}: {name}")
                
                # Show Excel data if available
                if self.excel_data and str(idx) in self.excel_data:
                    data = self.excel_data[str(idx)]
                    print(f"   💰 Preis: {data.get('preis', 'N/A')}")
                    print(f"   🏠 Zimmer: {data.get('zimmer', 'N/A')}")
                    print(f"   📍 Location: {data.get('location', 'N/A')}")
                    if 'link' in data:
                        print(f"   🔗 Link: {data['link']}")
                
                # Show distances if available
                if self.distances and str(idx) in self.distances:
                    dist = self.distances[str(idx)]
                    print(f"   ✈️  Flughafen: {dist.get('fl_min', 'N/A')} min")
                    print(f"   🌊 Daia: {dist.get('daia_min', 'N/A')} min")
                    
            else:
                print(f"❌ Property #{index} not found. Valid range: 1-{len(self.property_names)}")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def search_properties(self, term):
        """Search properties by name"""
        term = term.lower()
        matches = []
        
        for i, name in enumerate(self.property_names, 1):
            if term in name.lower():
                matches.append((i, name))
        
        if matches:
            print(f"\n🔍 Found {len(matches)} matches for '{term}':")
            print("-" * 60)
            for i, name in matches:
                print(f"{i:2d}. {name}")
        else:
            print(f"❌ No properties found matching '{term}'")
    
    def show_excel_data(self):
        """Show available Excel data summary"""
        if not self.excel_data:
            print("❌ No Excel data loaded")
            return
            
        print(f"\n📊 Excel Data Summary ({len(self.excel_data)} entries):")
        print("-" * 60)
        for key, data in self.excel_data.items():
            idx = int(key) + 1
            name = self.property_names[int(key)] if int(key) < len(self.property_names) else "Unknown"
            print(f"{idx:2d}. {data.get('preis', 'N/A')} € - {name[:50]}")
    
    def export_names(self, filename="property_names.txt"):
        """Export property names to text file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for i, name in enumerate(self.property_names, 1):
                    f.write(f"{i}. {name}\n")
            print(f"✅ Exported {len(self.property_names)} property names to {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def run(self):
        """Main TUI loop"""
        while True:
            try:
                choice = self.show_menu()
                
                if choice == "0":
                    print("👋 Auf Wiedersehen!")
                    break
                elif choice == "1":
                    self.list_properties()
                elif choice == "2":
                    index = input("Enter property number: ").strip()
                    self.show_property(index)
                elif choice == "3":
                    term = input("Search term: ").strip()
                    if term:
                        self.search_properties(term)
                elif choice == "4":
                    self.show_excel_data()
                elif choice == "5":
                    print("📍 Distances:", self.distances)
                elif choice == "6":
                    filename = input("Filename (Enter for default): ").strip()
                    if not filename:
                        filename = "property_names.txt"
                    self.export_names(filename)
                else:
                    print("❌ Invalid choice. Try again.")
                    
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("Press Enter to continue...")

if __name__ == "__main__":
    # Safe mode - never reads large HTML files
    print("🛡️  Running in SAFE MODE - no large file loading")
    tui = MallorcaTUI()
    tui.run()