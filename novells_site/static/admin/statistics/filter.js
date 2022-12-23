function Hide(){
if (document.getElementById('date_type').options[document.getElementById('date_type').selectedIndex].value == 'arbitrary_period'){
    document.getElementById('end_date').style.display = '';
    document.getElementById('end_date').required = true;
    document.getElementById('start_date').style.display = '';
    document.getElementById('start_date').required = true;
    }
else {
    document.getElementById('end_date').style.display = 'none';
    document.getElementById('start_date').style.display = 'none';
    }
}
window.onload = function(){
Hide()
document.getElementById('date_type').onchange = Hide;
        }
