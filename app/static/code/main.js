function darkMode() {
    var body = document.body;
    body.classList.toggle("dark-mode");
    if (body.classList.contains("dark-mode")) {
      document.getElementById("codeColor").href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.css";
    } else {
      document.getElementById("codeColor").href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/base16/atelier-cave-light.min.css";
    }
}
