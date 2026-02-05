import json
import os
import uuid
import datetime

DATA_FILE = "templates.json"

class DataHandler:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.ensure_data_file()

    def ensure_data_file(self):
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        except Exception as e:
            print(f"Error loading data: {e}")
            return []

    def save_data(self, data):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def add_template(self, title, content, category="General"):
        data = self.load_data()
        new_item = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "category": category,
            "timestamp":  datetime.datetime.now().isoformat()
        }
        data.append(new_item)
        self.save_data(data)
        return new_item

    def update_template(self, item_id, title, content, category):
        data = self.load_data()
        for item in data:
            if item.get('id') == item_id:
                item['title'] = title
                item['content'] = content
                item['category'] = category
                item['timestamp'] = datetime.datetime.now().isoformat()
                break
        self.save_data(data)

    def delete_template(self, item_id):
        data = self.load_data()
        data = [item for item in data if item.get('id') != item_id]
        self.save_data(data)

    def get_categories(self):
        data = self.load_data()
        categories = set()
        for item in data:
            cat = item.get('category')
            if cat:
                categories.add(cat)
        # Ensure standard options are present or handled in UI
        return sorted(list(categories))
