from flask import render_template
from st_webservice import app
from st_webservice.errors import bp

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(505)
def internal_error(error):
    app.db.session.rollback()
    return render_template('errors/500.html'), 500
