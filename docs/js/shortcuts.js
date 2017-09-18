document.onkeydown = function(event) {
  if (event.keyCode == 220) {  // "\" key
    var text_input = document.getElementById('q');
    text_input.focus();
    text_input.select();
    return false;
  }
}
