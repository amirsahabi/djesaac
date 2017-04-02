from flask import Flask

# create app
app = Flask(__name__)

# home
@app.route('/')
def home():
    return "Home"

# start server
if __name__ == "__main__":
    app.debug = True
    app.run(threaded=True, port=3000, host='0.0.0.0')
