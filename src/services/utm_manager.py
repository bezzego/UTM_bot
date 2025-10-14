import json
import os
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class UTMManager:
    def __init__(self, data_file: str = "data/utm_data.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self.ensure_data_file_exists()
        self.load_data()

    def ensure_data_file_exists(self):
        """Создает директорию и файл данных, если они не существуют"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            if not os.path.exists(self.data_file):
                initial_data = {
                    "sources": [],
                    "mediums": {
                        "publications": [],
                        "mailings": [],
                        "stories": [],
                        "channels": []
                    },
                    "campaigns": {
                        "spb": [],
                        "msk": [],
                        "tr": [],
                        "regions": [],
                        "foreign": []
                    }
                }
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error creating data file: {e}")

    def load_data(self):
        """Загружает данные из JSON файла"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.data = {
                "sources": [],
                "mediums": {"publications": [], "mailings": [], "stories": [], "channels": []},
                "campaigns": {"spb": [], "msk": [], "tr": [], "regions": [], "foreign": []}
            }

    def save_data(self):
        """Сохраняет данные в JSON файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False

    def get_all_categories(self) -> Dict:
        """Возвращает все категории для инлайн-клавиатуры"""
        return {
            "utm_source": ("📊 Источники трафика (utm_source)", "source"),
            "utm_medium_publications": ("📣 Публикации (utm_medium)", "medium_publications"),
            "utm_medium_mailings": ("📧 Рассылки (utm_medium)", "medium_mailings"),
            "utm_medium_stories": ("📱 Сторисы (utm_medium)", "medium_stories"),
            "utm_medium_channels": ("📡 Каналы (utm_medium)", "medium_channels"),
            "utm_campaign_spb": ("📍 СПБ кампании", "campaign_spb"),
            "utm_campaign_msk": ("🏙 МСК кампании", "campaign_msk"),
            "utm_campaign_tr": ("✈️ Турция кампании", "campaign_tr"),
            "utm_campaign_regions": ("🌍 Регионы кампании", "campaign_regions"),
            "utm_campaign_foreign": ("🌐 Зарубежье кампании", "campaign_foreign")
        }

    def get_category_data(self, category_key: str) -> List[Tuple[str, str]]:
        """Возвращает данные для конкретной категории"""
        category_map = {
            "source": ("sources", None),
            "medium_publications": ("mediums", "publications"),
            "medium_mailings": ("mediums", "mailings"),
            "medium_stories": ("mediums", "stories"),
            "medium_channels": ("mediums", "channels"),
            "campaign_spb": ("campaigns", "spb"),
            "campaign_msk": ("campaigns", "msk"),
            "campaign_tr": ("campaigns", "tr"),
            "campaign_regions": ("campaigns", "regions"),
            "campaign_foreign": ("campaigns", "foreign")
        }
        
        if category_key in category_map:
            main_key, sub_key = category_map[category_key]
            if sub_key:
                return self.data[main_key][sub_key]
            else:
                return self.data[main_key]
        return []

    def add_item(self, category_key: str, name: str, value: str) -> bool:
        """Добавляет новый элемент в категорию"""
        try:
            category_map = {
                "source": ("sources", None),
                "medium_publications": ("mediums", "publications"),
                "medium_mailings": ("mediums", "mailings"),
                "medium_stories": ("mediums", "stories"),
                "medium_channels": ("mediums", "channels"),
                "campaign_spb": ("campaigns", "spb"),
                "campaign_msk": ("campaigns", "msk"),
                "campaign_tr": ("campaigns", "tr"),
                "campaign_regions": ("campaigns", "regions"),
                "campaign_foreign": ("campaigns", "foreign")
            }
            
            if category_key not in category_map:
                return False
            
            main_key, sub_key = category_map[category_key]
            item = [name, value]
            
            if sub_key:
                # Проверяем на дубликаты
                existing_items = self.data[main_key][sub_key]
                if any(existing_item[1] == value for existing_item in existing_items):
                    return False
                self.data[main_key][sub_key].append(item)
            else:
                # Проверяем на дубликаты
                if any(existing_item[1] == value for existing_item in self.data[main_key]):
                    return False
                self.data[main_key].append(item)
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            return False

    def delete_item(self, category_key: str, value: str) -> bool:
        """Удаляет элемент из категории"""
        try:
            category_map = {
                "source": ("sources", None),
                "medium_publications": ("mediums", "publications"),
                "medium_mailings": ("mediums", "mailings"),
                "medium_stories": ("mediums", "stories"),
                "medium_channels": ("mediums", "channels"),
                "campaign_spb": ("campaigns", "spb"),
                "campaign_msk": ("campaigns", "msk"),
                "campaign_tr": ("campaigns", "tr"),
                "campaign_regions": ("campaigns", "regions"),
                "campaign_foreign": ("campaigns", "foreign")
            }
            
            if category_key not in category_map:
                return False
            
            main_key, sub_key = category_map[category_key]
            
            if sub_key:
                self.data[main_key][sub_key] = [
                    item for item in self.data[main_key][sub_key] 
                    if item[1] != value
                ]
            else:
                self.data[main_key] = [
                    item for item in self.data[main_key] 
                    if item[1] != value
                ]
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error deleting item: {e}")
            return False

# Глобальный экземпляр менеджера
utm_manager = UTMManager()