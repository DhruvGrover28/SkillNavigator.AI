import requests
import json

def test_remoteok_api():
    print("Testing RemoteOK API directly...")
    
    try:
        url = "https://remoteok.io/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Data type: {type(data)}")
                print(f"Data length: {len(data) if isinstance(data, list) else 'N/A'}")
                
                if isinstance(data, list) and len(data) > 1:
                    print("First few items:")
                    for i, item in enumerate(data[:3]):
                        print(f"{i}: {type(item)} - {item}")
                        
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Response text (first 200 chars): {response.text[:200]}")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_remoteok_api()