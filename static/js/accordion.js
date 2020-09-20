$(function() {
    var acc = document.getElementsByClassName("accordion");
    var i;

    for (i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function() {

            if (this.classList.contains('active')) {
                
                this.classList.remove('active');
                var panel = this.nextElementSibling;
                panel.style.display = "none";
            } 
            else {
                var p;
                for (p = 0; p < acc.length; p++) {
                    if (acc[p] !== this) {
                        acc[p].classList.remove('active');
                        var ppanel = acc[p].nextElementSibling;
                        ppanel.style.display = "none";
                    }
                }
                this.classList.add('active');
                var panel = this.nextElementSibling;
                panel.style.display = "block";
            }
        });
    }
})