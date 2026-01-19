import sys, os

sys.path.insert(0, '/var/www/html/dash_SampleTrack_Mercury')

os.chdir('/var/www/html/dash_SampleTrack_Mercury')

print("wsgi: Current Working Directory:",os.getcwd())

#from app import server as application

from app import app
application = app.server









#sys.stdout.reconfigure(encoding='utf-8')
#sys.stderr.reconfigure(encoding='utf-8')

# Also set environment variables for UTF-8
#os.environ["PYTHONIOENCODING"] = "utf-8"
#os.environ["LC_ALL"] = "C.UTF-8"
#os.environ["LANG"] = "C.UTF-8"