"""Interface webservice """

from smart_cv.interface import process_cv
from py2http import mk_app


app = mk_app([process_cv], publish_openapi=True, publish_swagger=True)

if __name__ == '__main__':
    app.run()
