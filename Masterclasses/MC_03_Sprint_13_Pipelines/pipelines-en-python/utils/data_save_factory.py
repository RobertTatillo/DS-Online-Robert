import json

class DataSaveFactory:
    def _save_txt(self, result, id):    
        with open(f"result_{id}.txt", "w") as f:
            for customer_id, category in result:
                f.write(f"{customer_id}, {category}\n")

    def _save_json(self, result, id):
        with open(f"result_{id}.json", "w", encoding = "utf-8") as f:
            json.dump(
                [{"customer_id": customer_id, "category": category} for customer_id, category in result],
                f,
                indent=4,
                ensure_ascii=False
            )

    def save_file(self, save_type, result, id):
        if save_type == "txt":
            self._save_txt(result=result, id=id)
        
        if save_type == "json":
            self._save_json(result=result, id=id)