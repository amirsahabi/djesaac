from flask import Flask, request, render_template
import youtube_dl
import databases

# create app
app = Flask(__name__)

# home
@app.route('/')
def home():
    # TODO: Add song listing functionality
    return render_template('home.html')

@app.route('/add/', methods=['GET','POST'])
def add():
    if(request.method == 'GET'):
        return render_template('add.html')
    else:
        return addSongToQueue(request.form['link'])

@app.route('/history/')
def history():
    # TODO: add history functionality
    return render_template('history.html')


def addSongToQueue(songLink):
    # TODO: add adding song to queue functionality
    return 0


# start server
if __name__ == "__main__":
    app.debug = True
    app.run(threaded=True, port=3000, host='0.0.0.0')
