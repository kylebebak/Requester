document.onkeydown = function(event) {
  if (event.keyCode == 220) {  // "\" key
    var text_input = document.getElementById('q');
    text_input.focus();
    text_input.select();
    return false;
  }
}

function toggleToc() {
  var toc = document.getElementById('toc-mobile');
  toc.style.display = toc.style.display === 'none' ? '' : 'none';
  var toggle = document.getElementById('toggle-toc');
  toggle.classList.toggle('open');
}
