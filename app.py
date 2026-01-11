from app import create_app
from app.models import db, login_manager
from app.routes import init_routes

app = create_app()
login_manager.init_app(app)
login_manager.login_view = 'login'

init_routes(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)