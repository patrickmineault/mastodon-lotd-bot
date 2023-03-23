from flask import Flask, request, render_template_string

app = Flask(__name__)


@app.route("/")
def index():
    return """Only used for oauth callback."""


@app.route("/callback")
def callback():
    code = request.args.get("code")
    # Use the code to get access_token
    return render_template_string(
        """
    <html>
        <head>
            <script>
                function copyCode() {
                    var codeElement = document.getElementById("code");
                    var range = document.createRange();
                    range.selectNode(codeElement);
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                    document.execCommand("copy");
                    window.getSelection().removeAllRanges();
                    
                    var messageElement = document.getElementById("message");
                    messageElement.innerHTML = "Code copied!";
                }
            </script>
        </head>
        <body>
            <p>Authorization code:</p>
            <pre id="code">{{ code }}</pre>
            <button onclick="copyCode()">Copy Code</button>
            <p id="message"></p>
        </body>
    </html>
    """,
        code=code,
    )


if __name__ == "__main__":
    app.run(port=8000)
