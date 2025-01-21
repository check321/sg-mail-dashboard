from ui.app import create_app

def main():
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main() 