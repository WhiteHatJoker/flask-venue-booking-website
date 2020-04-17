const deleteBtn = document.getElementById('delete-venue');
if(deleteBtn) {
    deleteBtn.onclick = function(e) {
        const venueId = e.target.dataset['id'];
        fetch('/venues/' + venueId, {
            method: 'DELETE'
        }).then(function (response) {
            return response.json();
        }).then(function (jsonResponse) {
            if(jsonResponse['success']) {
                console.log(jsonResponse['success']);
                document.location.href="/venues";
            } else {
                console.log(jsonResponse['success']);
                document.location.href="/venues/"+venueId;
            }
        }).catch(function() {
            console.log('Error');
            document.location.href="/venues/"+venueId;
        });
    }
}

function hideSeeking(checkBox, hideField) {
    if (checkBox.checked == true){
        hideField.style.display = "block";
    } else {
        hideField.style.display = "none";
    }
}

const checkBx = document.querySelector('input#seeking_talent');
const checkBx2 = document.querySelector('input#seeking_venue');
const seekingTextField = document.getElementById('seeking_description_field');
if (checkBx) {
    checkBx.addEventListener('click', function () {  hideSeeking(checkBx, seekingTextField) });
} else if(checkBx2) {
    checkBx.addEventListener('click', function () {  hideSeeking(checkBx2, seekingTextField) });
}



