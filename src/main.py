from ui.app import create_app
import json

def main():
    app = create_app()
    # read username and password from config/auth.json
    # 从auth.json读取认证信息
    with open('config/auth.json', 'r', encoding='utf-8') as f:
        auth_config = json.load(f)
        username = auth_config['ui_auth'].get('username', 'admin')
        password = auth_config['ui_auth'].get('password', 'admin')
    
    app.launch(server_name="0.0.0.0", server_port=7860, auth=(username, password))

if __name__ == "__main__":
    main() 