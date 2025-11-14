from flask import Flask, redirect , render_template , request, url_for
app = Flask(__name__)

@app.route('/home')
def home():
    return render_template('home.html')    

if __name__ == '__main__':
    app.run(debug=True , port=8000)