import os
import json
import time

class FileQueue:
    def __init__(self, queue_file="task_queue.json"):
        self.queue_file = queue_file
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, "w") as f:
                json.dump([], f)

    def push(self, task_data):
        try:
            with open(self.queue_file, "r+") as f:
                tasks = json.load(f)
                tasks.append(task_data)
                f.seek(0)
                json.dump(tasks, f)
                f.truncate()
            return True
        except Exception as e:
            print(f"Error pushing to file queue: {e}")
            return False

    def pop(self):
        try:
            if not os.path.exists(self.queue_file):
                return None
            
            with open(self.queue_file, "r+") as f:
                tasks = json.load(f)
                if not tasks:
                    return None
                task = tasks.pop(0)
                f.seek(0)
                json.dump(tasks, f)
                f.truncate()
                return task
        except Exception as e:
            print(f"Error popping from file queue: {e}")
            return None

class StatusStore:
    def __init__(self, status_file="status_store.json"):
        self.status_file = status_file
        if not os.path.exists(self.status_file):
            with open(self.status_file, "w") as f:
                json.dump({}, f)

    def set(self, key, value):
        try:
            with open(self.status_file, "r+") as f:
                data = json.load(f)
                data[key] = value
                f.seek(0)
                json.dump(data, f)
                f.truncate()
        except Exception as e:
            print(f"Error setting status: {e}")

    def get(self, key):
        try:
            with open(self.status_file, "r") as f:
                data = json.load(f)
                return data.get(key)
        except Exception:
            return None
