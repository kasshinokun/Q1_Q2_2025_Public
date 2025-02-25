# Initially Flask, but it can change 
# created on 2025-01-23
# release 1_23_01_2025

from flask import Flask, render_template      

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("JS_APP/about_flask.ejs")
    
@app.route("/user")
def care_user():
    return "Hello, User"
    
if __name__ == "__main__":
    app.run(debug=True)
  
