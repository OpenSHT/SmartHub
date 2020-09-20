$(document).ready(function (value) {
    
    $('#small-float').on('click', function (e) {
        var x = document.getElementById("sidebar");
        var butt = document.getElementById("small-float");
        var icon = document.getElementById("sm-icon")

        if (this.classList.contains("active")) {
            this.className = this.className.replace(" active", "");
            x.style.display = "none";
            butt.style.left = '40px';

            icon.classList.remove("fa-chevron-left")
            icon.classList.add("fa-chevron-right");

        } else {
            this.className += " active";
            x.style.display = 'block';
            butt.style.left = 'calc(290px + 10%)';
            icon.classList.remove("fa-chevron-right")
            icon.classList.add("fa-chevron-left");        }
    });
    $('#big-float').on('click', function (e) {
        var x = document.getElementById("sidebar");
        var butt = document.getElementById("big-float");
        var icon = document.getElementById("bg-icon")

        if (this.classList.contains("active")) {
            this.className = this.className.replace(" active", "");
            x.style.display = "none";
            butt.style.left = '40px';

            icon.classList.remove("fa-chevron-left")
            icon.classList.add("fa-chevron-right");

        } else {
            this.className += " active";
            x.style.display = 'block';
            butt.style.left = 'calc(290px + 10%)';
            icon.classList.remove("fa-chevron-right")
            icon.classList.add("fa-chevron-left");        }
    });
});

function showChooser(choice, element) {
    if (choice === 'color') {
        document.getElementById('hidden_choice_1').style.display = 'block'
        document.getElementById('hidden_choice_2').style.display = 'none'
    } else {
        document.getElementById('hidden_choice_2').style.display = 'block'
        document.getElementById('hidden_choice_1').style.display = 'none'
    }
};

