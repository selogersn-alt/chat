import urllib.request
import json

url = "https://logersenegal.com/api/properties/"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        if isinstance(data, dict) and 'results' in data:
            print(json.dumps(data['results'][:2], indent=2))
        else:
            print(json.dumps(data[:2], indent=2))
except Exception as e:
    print(f"Error: {e}")
