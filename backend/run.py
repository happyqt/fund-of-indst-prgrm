"""
Модуль для запуска backend сервера
"""
from app import create_app
from app.database import init_db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print("Attempting to initialize database...")
        try:
            init_db()
            print("Database initialization routine finished.")
        except Exception as e:
            print(f"Error during database initialization: {e}")
    app.run(host='0.0.0.0', port=5000, debug=True)
