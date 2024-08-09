from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__, static_url_path="/static", static_folder="static")

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:62645526@localhost:3306/hopacDBS'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 't83nf9KG*&@!orjy6&5%' 

    # for any file upload mainly pictures
    app.config['UPLOAD_FOLDER'] = 'uploads'

    # For sending email to the user
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'mcmillans254@gmail.com'
    app.config['MAIL_PASSWORD'] = 'jvht ztng xiro swic'
    app.config['MAIL_DEFAULT_SENDER'] = 'mcmillans254@gmail.com'


   # login_manager = LoginManager(app)
    #login_manager.login_view = 'login'
  
    db.init_app(app)
    mail.init_app(app)
    # Import and register blueprints or routes
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint, url_path='/main_blueprint')

    
    return app
